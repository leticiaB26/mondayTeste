import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

# Cole os dados do seu painel do Supabase (Project Settings > API)
SUPABASE_URL = "https://dbjfutvveqmznswpfhuz.supabase.co"
SUPABASE_KEY = "sb_publishable_caLtR7pPHeIL5pwKOMiKpg_Rh6w0laA"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Monday Clone API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SCHEMAS (PYDANTIC) ---
class TaskCreate(BaseModel):
    group_id: str
    title: str
    status: Optional[str] = "Não Iniciado"
    priority: Optional[str] = "Média"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_name: Optional[str] = None
    due_date: Optional[str] = None

# --- ROTAS DA API ---
@app.get("/")
def test_connection():
    return {"status": "sucesso", "mensagem": "API Monday conectada com sucesso ao Supabase!"}

@app.get("/boards")
def get_boards():
    try:
        # Busca os quadros no Supabase
        boards_res = supabase.table("boards").select("*").execute()
        boards = boards_res.data

        # Se o banco estiver vazio, cria o quadro inicial com grupos e tarefas
        if not boards:
            board_id = str(uuid.uuid4())
            new_board = {"id": board_id, "title": "Meu Quadro na Nuvem"}
            supabase.table("boards").insert(new_board).execute()

            g1_id = str(uuid.uuid4())
            g2_id = str(uuid.uuid4())
            groups = [
                {"id": g1_id, "board_id": board_id, "title": "Em Andamento", "color": "blue"},
                {"id": g2_id, "board_id": board_id, "title": "Próximas Tarefas", "color": "purple"}
            ]
            supabase.table("groups").insert(groups).execute()

            tasks = [
                {"id": str(uuid.uuid4()), "group_id": g1_id, "title": "Configurar Supabase", "status": "Feito", "priority": "Alta"},
                {"id": str(uuid.uuid4()), "group_id": g1_id, "title": "Conectar Equipe", "status": "Em Andamento", "priority": "Média"}
            ]
            supabase.table("tasks").insert(tasks).execute()

            boards = [new_board]

        # Monta a estrutura de resposta para o front-end
        result = []
        for b in boards:
            groups_res = supabase.table("groups").select("*").eq("board_id", b["id"]).execute()
            groups = groups_res.data
            
            groups_data = []
            for g in groups:
                tasks_res = supabase.table("tasks").select("*").eq("group_id", g["id"]).execute()
                tasks = tasks_res.data

                formatted_tasks = [{
                    "id": t["id"],
                    "title": t["title"],
                    "status": t.get("status", "Não Iniciado"),
                    "priority": t.get("priority", "Média"),
                    "assignee": t.get("assignee_name", "Pessoa"),
                    "dueDate": t.get("due_date", "")
                } for t in tasks]

                groups_data.append({
                    "id": g["id"],
                    "title": g["title"],
                    "color": g.get("color", "blue"),
                    "tasks": formatted_tasks
                })

            result.append({
                "id": b["id"],
                "title": b["title"],
                "groups": groups_data
            })

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tasks")
def create_task(task: TaskCreate):
    try:
        new_task = {
            "id": str(uuid.uuid4()),
            "group_id": task.group_id,
            "title": task.title,
            "status": task.status,
            "priority": task.priority
        }
        res = supabase.table("tasks").insert(new_task).execute()
        return res.data[0] if res.data else new_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/tasks/{task_id}")
def update_task(task_id: str, task_data: TaskUpdate):
    try:
        update_dict = {k: v for k, v in task_data.dict().items() if v is not None}
        if "assignee_name" in update_dict:
            update_dict["assignee_name"] = update_dict.pop("assignee_name")
            
        supabase.table("tasks").update(update_dict).eq("id", task_id).execute()
        return {"status": "atualizado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    try:
        supabase.table("tasks").delete().eq("id", task_id).execute()
        return {"status": "eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)