# Otomasi Absen Stupor
**API otomasi absensi stupor UNPAR** 
Program buat yang suka lupa absen

Tech Stack :
- **Lib** : Selenium, FastAPI
- **Env** : GC Run, GC Scheduler, GC Tasks (mobile HTTP Shortcuts)

## Instalasi
1. **Clone Repo**
```bash
git clone https://github.com/mkeaudric/otomasi-absen-stupor.git
cd otomasi-absen-stupor
```

2. **Instalasi Library**
```bash
pip install -r requirements.txt
```
Gw saranin pake `venv`.

Untuk run lokal, bisa setup `.env` untuk email dan password
```bash
STUPOR_EMAIL={email@unpar.ac.id}
STUPOR_PASS={password}
```
Jika tidak mau install `google-cloud-tasks protobuf`, hapus aja bagian import & endpoint scheduler.
> [!warning]
> Kalau fork project, pastikan ada `.env` di `.gitignore` (udah ada tapi bisi kehapus pas mau ngepush).

## Deploy ke GC
Upload : `Dockerfile`, `absenStupor.py`, `.dockerignore`, `requirements.txt`

Deploy ke GC Run :
```bash
gcloud run deploy selenium-absen-stupor --source . --region asia-southeast2 --allow-unauthenticated --memory 2Gi
```
Pakai `1Gi` juga gpp

## Cara Pakai
### Desktop
Masukan jadwal fix ke GC Scheduler
- **Target URL** : `https://[URL-Cloud-Run]/api/absen`
- **Method** : POST
- Format jam pakai **cron** (Contoh : Selasa jam 7.30 -> `30 7 * * 2`)
  Saran gua, beda hari atau jam berbeda dengan menit berbeda pakai Task terpisah (karena penulisan Cron is so fucking unflexible).

### Mobile 
Jam di luar jadwal (misal jadwal pengganti) utama bisa pakai **HTTP Shortcuts**
1. Aktifkan **API Cloud Tasks**
2. Bikin variabel baru (Input text)
3. Bikin shortcut (Create from scratch)
    - **HTTP Method** : POST
    - **URL** : URL-Cloud-Run
    - **Request Body / Parameter** : `{ "waktu_eksekusi": "YYYY-MM-DD HH:MM:SS" }`
4. Jalanin shortcut untuk membuat task baru.

## Lisensi
Tidak ada. Silahkan fork, copas, atau dimodifikasi sakarepmu.
