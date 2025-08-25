# Restore Frontend (Berani)

## Prereqs
- Node LTS and npm
- Expo CLI
- EAS CLI

## Install and run
npm install
npx expo start -c

## Required config (already embedded in app.config.ts)
extra.API_BASE_URL = https://berani-backend.onrender.com
extra.REPORT_PATH  = /report
extra.CHAT_PATH    = /chat

## For EAS builds (optional)
eas secret:create --scope project --name API_BASE_URL --value "https://berani-backend.onrender.com"
eas secret:create --scope project --name REPORT_PATH   --value "/report"
eas secret:create --scope project --name CHAT_PATH     --value "/chat"

## Health check (manual)
Open New Report → Generate (should fill AI Report)
Open AI Assistant → send message (should reply)
