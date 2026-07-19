# Winter AI — Backend

Multi-paradigm reasoning engine by **INEZA Aime Bruno**, Rwanda.  
Responds in **English, French, and Kinyarwanda**.

## Deploy on Render

1. Push this folder to a GitHub repo
2. Go to [render.com](https://render.com) → New → Web Service → Docker
3. Connect your GitHub repo
4. Set environment variable:
   - `FRONTEND_URL` = your Vercel frontend URL (e.g. `https://winter-ai.vercel.app`)
5. Deploy ✅

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chats/message` | Chat with Winter AI |
| POST | `/api/v1/brain/update` | Update main knowledge base |
| POST | `/api/v1/knowledge/upload` | Upload new `.txt` or `.md` knowledge file |
| GET | `/api/v1/knowledge/list` | List all knowledge files |
| GET | `/api/v1/knowledge/{filename}` | Read a specific knowledge file |
| GET | `/api/v1/brain` | Read brain.txt |
| GET | `/api/v1/health` | Health check |
| GET | `/docs` | Swagger UI |

## Teaching Winter AI

Send a POST to `/api/v1/brain/update` with JSON:
```json
{
  "content": "EN: Python was created in 1991. | FR: Python a été créé en 1991. | RW: Python yashojwe mu 1991."
}
```

Or upload a `.txt` file via `/api/v1/knowledge/upload`.

Each knowledge line should follow this format:
```
EN: English fact here. | FR: French fact here. | RW: Kinyarwanda fact here.
```
