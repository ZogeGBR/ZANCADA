"""Prueba v4 (TIF): dispatch real de PTB + SDK real de google-genai (HTTP simulado) + Open-Meteo simulado + SQLite real."""
import asyncio, json, os, sys, tempfile, logging
import httpx, httpx2
os.environ.update(TELEGRAM_TOKEN="123:ABC", GEMINI_API_KEY="k"); os.environ.pop("GEMINI_MODEL", None)
DBFILE = os.path.join(tempfile.mkdtemp(), "t.db")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import telegram, telegram.ext
from telegram import Update, Bot
logging.disable(logging.CRITICAL)
ok = fail = 0
def check(n, c, d=""):
    global ok, fail
    if c: ok += 1; print("PASS ", n)
    else: fail += 1; print("FAIL ", n, d)

caps = []; modo = {"v": "ok", "meteo": "ok"}
def texto_final(t): return {"id": "i", "status": "completed", "steps": [{"type": "model_output", "content": [{"type": "text", "text": t}]}]}
def fake_gemini(request):
    body = json.loads(request.content or b"{}"); caps.append(body)
    if modo["v"] == "500": return httpx2.Response(500, json={"error": {"code": 500, "message": "x", "status": "INTERNAL"}}, request=request)
    entrada = body["input"]; ult = entrada[-1]
    if body.get("response_format"):  # extracción estructurada
        txt = json.dumps(modo.get("extr", {"entendido": True, "km": 8, "minutos": 44, "tipo": "rodaje", "notas": None}))
        return httpx2.Response(200, json=texto_final(txt), request=request)
    if modo["v"] == "bucle":
        return httpx2.Response(200, json={"id": "i", "status": "requires_action", "steps": [{"type": "function_call", "id": "c1", "name": "calcular_ritmo", "arguments": {"distancia_km": 5, "tiempo": "25:00"}}]}, request=request)
    if ult["type"] == "function_result":
        return httpx2.Response(200, json=texto_final("FINAL:" + ult["result"][:300]), request=request)
    t = ult["content"][0]["text"]
    if modo["v"] == "bucle":
        return httpx2.Response(200, json={"id": "i", "status": "requires_action", "steps": [{"type": "function_call", "id": "c1", "name": "calcular_ritmo", "arguments": {"distancia_km": 5, "tiempo": "25:00"}}]}, request=request)
    llamada = None
    if "clima" in t: llamada = ("clima_para_correr", {"ciudad": "Mendoza"})
    elif "corrí" in t: llamada = ("registrar_entrenamiento", {"distancia_km": 5, "tiempo": "25:00", "tipo": "rodaje"})
    elif "semana" in t and "plan" not in t.lower(): llamada = ("resumen_entrenamientos", {"dias": 7})
    elif "ritmo5" in t: llamada = ("calcular_ritmo", {"distancia_km": 5, "tiempo": "abc"})
    if llamada:
        return httpx2.Response(200, json={"id": "i", "status": "requires_action", "steps": [
            {"type": "thought", "signature": "c2ln"},
            {"type": "function_call", "id": "call1", "name": llamada[0], "arguments": llamada[1]}]}, request=request)
    return httpx2.Response(200, json=texto_final(f"RESP({t[:40]})"), request=request)
def fake_meteo(request):
    if modo["meteo"] == "caida": raise httpx.ConnectError("sin red")
    u = str(request.url)
    if "geocoding" in u:
        if "Nowhere" in u: return httpx.Response(200, json={}, request=request)
        return httpx.Response(200, json={"results": [{"name": "Mendoza", "country": "Argentina", "latitude": -32.9, "longitude": -68.8}]}, request=request)
    horas = [f"2026-11-12T{h:02d}:00" for h in range(24)]
    return httpx.Response(200, json={"hourly": {"time": horas, "temperature_2m": [5 + h for h in range(24)],
        "precipitation_probability": [0]*24, "wind_speed_10m": [5]*24}}, request=request)
async def a_send2(self, request, **k): return fake_gemini(request)
def s_send2(self, request, **k): return fake_gemini(request)
async def a_send(self, request, **k): return fake_meteo(request)
def s_send(self, request, **k): return fake_meteo(request)
httpx2.AsyncClient.send = a_send2; httpx2.Client.send = s_send2
httpx.AsyncClient.send = a_send; httpx.Client.send = s_send

import db, llm, bot as zbot
db.RUTA_DB = DBFILE
env = []; edits = []
async def fake_post(self, endpoint, data=None, *a, **k):
    if endpoint == "getMe": return {"id": 99, "is_bot": True, "first_name": "Z", "username": "Z_bot"}
    if endpoint == "sendMessage":
        env.append(data["text"]); return {"message_id": 1, "date": 0, "chat": {"id": 1, "type": "private"}, "text": data["text"]}
    if endpoint == "editMessageText": edits.append(data["text"]); return True
    if endpoint == "getFile": return {"file_id": "f", "file_unique_id": "u", "file_path": "x.jpg"}
    return True
Bot._post = fake_post
async def fake_dl(self, *a, **k): return bytearray(b"\xff\xd8fakejpg")
telegram.File.download_as_bytearray = fake_dl
USER = {"id": 7, "is_bot": False, "first_name": "Zoe"}; CHAT = {"id": 7, "type": "private"}
uid = [0]
async def enviar(texto, cmd=False, app=None, extra=None):
    uid[0] += 1; env.clear()
    m = {"message_id": 1, "date": 0, "chat": CHAT, "from": USER, "text": texto, **(extra or {})}
    if cmd: m["entities"] = [{"type": "bot_command", "offset": 0, "length": len(texto.split()[0])}]
    await app.process_update(Update.de_json({"update_id": uid[0], "message": m}, app.bot)); return list(env)
async def boton(data, app):
    uid[0] += 1; env.clear(); edits.clear()
    cb = {"id": "1", "from": USER, "chat_instance": "c", "data": data,
          "message": {"message_id": 5, "date": 0, "chat": CHAT, "text": "x"}}
    await app.process_update(Update.de_json({"update_id": uid[0], "callback_query": cb}, app.bot)); return list(env), list(edits)

async def main():
    cap = {}
    telegram.ext.Application.run_polling = lambda self, **k: cap.update(app=self)
    zbot.TELEGRAM_TOKEN = "123:ABC"; zbot.main(); app = cap["app"]
    await app.initialize(); await app.post_init(app)
    # --- Function calling: clima
    r = await enviar("¿Cómo está el clima para correr hoy?", app=app)
    check("FC clima: respuesta final tras la herramienta", r and r[0].startswith("FINAL:") and "Mendoza" in r[0] and "mejores_horas" in r[0], r)
    c1, c2 = caps[-2], caps[-1]
    check("ronda 1 declara las 4 herramientas", [t["name"] for t in c1["tools"]] == ["clima_para_correr", "calcular_ritmo", "registrar_entrenamiento", "resumen_entrenamientos"])
    tipos = [s["type"] for s in c2["input"]]
    check("ronda 2 reenvia user_input, thought, function_call, function_result", tipos == ["user_input", "thought", "function_call", "function_result"], tipos)
    check("ronda 2 conserva la firma del thought", c2["input"][1].get("signature") == "c2ln", c2["input"][1])
    fr = c2["input"][-1]
    check("function_result trae call_id y name", fr["call_id"] == "call1" and fr["name"] == "clima_para_correr" and isinstance(fr["result"], str), fr)
    check("store=False en todas las rondas", c1["store"] is False and c2["store"] is False)
    check("el clima elige horas del dia (3 mejores, 5-22h)", '"hora"' in fr["result"] and fr["result"].count('"hora"') == 3, fr["result"][:200])
    check("se guardó solo el intercambio final en el historial", len(await db.obtener_historial(7, 20)) == 2)
    # --- Open-Meteo caído / ciudad inexistente: la herramienta no rompe
    modo["meteo"] = "caida"; r = await enviar("¿clima hoy?", app=app)
    check("Open-Meteo caído -> Gemini recibe error y el bot responde", r and "No pude ejecutar clima_para_correr" in caps[-1]["input"][-1]["result"], caps[-1]["input"][-1])
    modo["meteo"] = "ok"
    from tools import ejecutar_herramienta
    check("ciudad inexistente -> error legible", "No encontré" in (await ejecutar_herramienta("clima_para_correr", {"ciudad": "Nowhere"}, 7))["error"])
    check("herramienta con argumentos inválidos -> error", "error" in (await ejecutar_herramienta("calcular_ritmo", {"distancia_km": 5, "tiempo": "abc"}, 7)))
    check("herramienta desconocida -> error", "desconocida" in (await ejecutar_herramienta("hackear", {}, 7))["error"])
    check("registrar con distancia absurda -> error", "error" in (await ejecutar_herramienta("registrar_entrenamiento", {"distancia_km": 99999, "tiempo": "10:00"}, 7)))
    # --- Function calling: registrar y resumir (SQLite)
    r = await enviar("Hoy corrí 5 km en 25 minutos", app=app)
    check("FC registrar guarda en SQLite", (await db.resumen_entrenamientos(7, 7))["km_totales"] == 5.0)
    r = await enviar("¿cómo me fue esta semana?", app=app)
    check("FC resumen devuelve lo guardado", '"km_totales": 5.0' in caps[-1]["input"][-1]["result"], caps[-1]["input"][-1]["result"][:120])
    check("el user_id lo pone el bot (no el modelo)", "user_id" not in json.dumps(caps[-2]["tools"]))
    # --- Bucle infinito de herramientas -> corte
    modo["v"] = "bucle"; r = await enviar("loop", app=app)
    check("bucle de herramientas se corta con mensaje amable", r and "Tuve un problema" in r[0], r)
    modo["v"] = "ok"
    # --- Extracción estructurada de texto
    r = await enviar("/registrar hoy corrí 8 km en 44 minutos", cmd=True, app=app)
    check("/registrar propone con ritmo calculado", r and "8 km en 44:00" in r[0] and "5:30" in r[0], r)
    check("la extracción usa response_format JSON con esquema", caps[-1]["response_format"]["mime_type"] == "application/json" and "properties" in caps[-1]["response_format"]["schema"], caps[-1].get("response_format"))
    antes = (await db.resumen_entrenamientos(7, 7))["salidas"]
    _, ed = await boton("entreno:si", app)
    check("botón Guardar inserta el entrenamiento", (await db.resumen_entrenamientos(7, 7))["salidas"] == antes + 1 and "Guardado" in ed[0], ed)
    _, ed = await boton("entreno:si", app)
    check("doble clic no duplica", (await db.resumen_entrenamientos(7, 7))["salidas"] == antes + 1 and "ya no está" in ed[0], ed)
    await enviar("/registrar 3 km en 20", cmd=True, app=app)
    _, ed = await boton("entreno:no", app)
    check("botón Descartar no guarda", (await db.resumen_entrenamientos(7, 7))["salidas"] == antes + 1 and "Descartado" in ed[0], ed)
    modo["extr"] = {"entendido": False}
    r = await enviar("/registrar me duele la rodilla", cmd=True, app=app)
    check("texto que no es entrenamiento -> pide reintentar", "No pude sacar" in r[0], r)
    modo["extr"] = {"entendido": True, "km": -5, "minutos": 10, "tipo": "rodaje"}
    r = await enviar("/registrar x", cmd=True, app=app)
    check("km negativo -> rechazado por validación", "No pude sacar" in r[0], r)
    modo["extr"] = {"km": "mucho"}
    r = await enviar("/registrar x", cmd=True, app=app)
    check("JSON fuera de esquema -> rechazado", "No pude sacar" in r[0], r)
    modo.pop("extr")
    r = await enviar("/registrar", cmd=True, app=app); check("/registrar sin texto -> ayuda", "Contame" in r[0])
    # --- Foto (multimodal)
    r = await enviar("", app=app, extra={"text": None, "photo": [{"file_id": "a", "file_unique_id": "a", "width": 10, "height": 10}, {"file_id": "b", "file_unique_id": "b", "width": 100, "height": 100}], "caption": "mi salida"})
    img = [p for p in caps[-1]["input"][0]["content"] if p["type"] == "image"]
    check("foto -> se envía imagen base64 a Gemini", len(img) == 1 and img[0]["mime_type"] == "image/jpeg" and img[0]["data"], caps[-1])
    check("foto -> propone entrenamiento con botones", r and "¿Lo guardo?" in r[0], r)
    # --- /resumen
    r = await enviar("/resumen", cmd=True, app=app)
    check("/resumen lista salidas y totales", "salidas" in r[0] and "km" in r[0], r)
    # --- /plan guiado
    r = await enviar("/plan", cmd=True, app=app); check("/plan pregunta la distancia", "distancia" in r[0], r)
    r, ed = await boton("plan:10K", app); check("elige 10K y pasa a semanas", "semanas" in r[0] and "10K" in ed[0], (r, ed))
    r = await enviar("mucho", app=app); check("semanas inválidas -> repregunta", "entre 2 y 24" in r[0], r)
    r = await enviar("8", app=app); check("semanas ok -> pregunta días", "días por semana" in r[0], r)
    r = await enviar("9", app=app); check("días inválidos -> repregunta", "entre 2 y 6" in r[0], r)
    r = await enviar("4", app=app)
    check("plan generado con Gemini", r and r[0].startswith("RESP(") and "10K" in caps[-1]["input"][-1]["content"][0]["text"] and "8 semanas" in caps[-1]["input"][-1]["content"][0]["text"], r)
    r = await enviar("/plan", cmd=True, app=app); r = await enviar("/cancelar", cmd=True, app=app)
    check("/cancelar sale del flujo", "cancelado" in r[0], r)
    r = await enviar("hola otra vez", app=app); check("tras cancelar, el chat vuelve a Gemini", r[0].startswith("RESP("), r)
    # --- Errores y limpieza
    modo["v"] = "500"; r = await enviar("¿clima?", app=app); check("Gemini caído -> aviso amable", "Tuve un problema" in r[0], r); modo["v"] = "ok"
    r = await enviar("/ritmo 10 52:30", cmd=True, app=app); check("/ritmo de v1 sigue funcionando", "5:15" in r[0], r)
    r = await enviar("/borrar_entrenos", cmd=True, app=app); check("/borrar_entrenos limpia", (await db.resumen_entrenamientos(7, 7))["salidas"] == 0, r)
    await db.guardar_entrenamiento(8, 5, 25); check("entrenamientos aislados por usuario", (await db.resumen_entrenamientos(7, 7))["salidas"] == 0 and (await db.resumen_entrenamientos(8, 7))["salidas"] == 1)
    r = await enviar("/help", cmd=True, app=app); check("/help lista comandos nuevos", all(c in r[0] for c in ("/registrar", "/resumen", "/plan")))
    await app.shutdown()
    print(f"\nRESULTADO: {ok} pass, {fail} fail")
asyncio.run(main())
