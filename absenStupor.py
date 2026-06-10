import os, time, datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

load_dotenv()
EMAIL = os.getenv("STUPOR_EMAIL")
PASSWORD = os.getenv("STUPOR_PASS")

app = FastAPI(title="API Otomasi Absensi Stupor")

class ResponAbsen(BaseModel):
    status: str
    message: str

@app.post("/api/absen", response_model=ResponAbsen)
def absen():
    opt = Options()
    # https://peter.sh/experiments/chromium-command-line-switches/
    opt.add_argument("--headless=new") # no UI 
    # --headless vs --headless=new (https://stackoverflow.com/questions/45631715/downloading-with-chrome-headless-and-selenium/73840130#73840130)
    opt.add_argument("--window-size=1920, 1080")
    opt.add_argument("--disable-gpu")
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=opt)

    try:
        driver.get("https://studentportal.unpar.ac.id")

        login_btn = driver.find_element(By.ID, "login-button")
        login_btn.click()
        time.sleep(0.5)

        driver.switch_to.active_element.send_keys(EMAIL)
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        time.sleep(0.5)

        driver.switch_to.active_element.send_keys(PASSWORD)
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        time.sleep(0.5)

        driver.get("https://studentportal.unpar.ac.id/jadwal")
        time.sleep(2)

        xpath_tombol_aktif = "//a[contains(@class, 'btn-danger') and .//i[contains(@class, 'fa-sign-in-alt')]]"
        
        try:
            # tunggu >=1 tombol absen aktif
            WebDriverWait(driver, 240).until(
                EC.presence_of_element_located((By.XPATH, xpath_tombol_aktif))
            )
            
            # berapa jadwal yang harus diabsen (yg jam nya sama)
            tombol_aktif = driver.find_elements(By.XPATH, xpath_tombol_aktif)
            jumlah_absen = len(tombol_aktif)
            print(f"Menemukan {jumlah_absen} jadwal untuk diabsen.")

            # sekaligus satu sesi
            for i in range(jumlah_absen):
                tombol_sekarang = driver.find_elements(By.XPATH, xpath_tombol_aktif)[i]
                
                # Absen
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(tombol_sekarang)).click()
                print(f"Menekan tombol absen jadwal ke-{i+1}...")
                
                # Presensi
                xpath_btn_presensi = "//button[contains(@class, 'swal-button--confirm') and text()='Presensi']"
                btn_presensi = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath_btn_presensi))
                )
                btn_presensi.click()
                
                # OK
                xpath_btn_ok = "//button[contains(@class, 'swal-button--confirm') and text()='OK']"
                btn_ok = WebDriverWait(driver, 300).until(
                    EC.element_to_be_clickable((By.XPATH, xpath_btn_ok))
                )
                btn_ok.click()
                print(f"Absen jadwal ke-{i+1} sukses!")
                
                # jeda dikit, kalo ada jadwal lain
                time.sleep(2)

            return ResponAbsen(
                status="success", 
                message=f"Berhasil memproses {jumlah_absen} absensi serentak."
            )

        except Exception as e:
            # timeout 30 detik
            raise HTTPException(status_code=400, detail=f"Gagal absen atau tombol belum aktif. Error: {str(e)}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500)
    finally:
        driver.quit()

class JadwalRequest(BaseModel):
    waktu_eksekusi: str  # "YYYY-MM-DD HH:MM:SS"

@app.post("/api/schedule")
def schedule_task(req: JadwalRequest):
    client = tasks_v2.CloudTasksClient()
    
    # config
    project = "selenium-absen-stupor"
    queue = "antrian-absen"
    location = "asia-southeast2"
    url_target = "https://selenium-absen-stupor-643866615049.asia-southeast2.run.app/api/absen"

    parent = client.queue_path(project, location, queue)

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url_target,
        }
    }

    # WIB -> UTC
    try:
        waktu_wib = datetime.datetime.strptime(req.waktu_eksekusi, "%Y-%m-%d %H:%M:%S")
        waktu_utc = waktu_wib - datetime.timedelta(hours=7)
        
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(waktu_utc)
        task["schedule_time"] = timestamp
    except ValueError:
        raise HTTPException(status_code=400, detail="Format waktu salah. Gunakan YYYY-MM-DD HH:MM:SS")

    response = client.create_task(request={"parent": parent, "task": task}) # buat debug aja
    
    return {
        "status": "success", 
        "message": f"Sukses! Absen darurat dijadwalkan pada {req.waktu_eksekusi} WIB."
    }
