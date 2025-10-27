#!/usr/bin/env python3
"""
Painel de gestão para o MonitoramentoBKP
Usa somente bibliotecas nativas (Tkinter, subprocess, json, os, threading, time...)
Salva em versao.config e config_cache.json para integração com o launcher/updater.
"""

import os
import json
import subprocess
import threading
import time
import urllib.request
import random
import webbrowser
from datetime import datetime, timedelta
from tkinter import (
    Tk, Frame, Label, Button, Text, Scrollbar, Listbox, Entry, StringVar,
    END, LEFT, RIGHT, BOTH, Y, X, TOP, BOTTOM, ttk, messagebox, filedialog
)

# ------------- Config (ajuste se necessário) -------------
CONFIG_URL = "https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/config.json"
BASE_DIR = r"C:\Program Files (x86)\MonitoramentoBKP"
LOG_BASE_DIR = os.path.join(BASE_DIR, "logs")
LAUNCHER_LOG = os.path.join(LOG_BASE_DIR, "launcher.log")
VERSION_FILE = os.path.join(BASE_DIR, "versao.config")        # JSON { "versao": "...", "tipo": "SERVIDOR", "filial": "..." }
CONFIG_CACHE = os.path.join(BASE_DIR, "config_cache.json")    # cache do config remoto
CHECK_CONFIG_INTERVAL = 60  # segundos para auto refresh de config quando solicitado pelo painel
LOG_TAIL_LINES = 200
AUTO_REFRESH_LOG_SECONDS = 5
# --------------------------------------------------------

# Colors / theme (light / modern)
BG = "#f5f7fa"
CARD = "#ffffff"
ACCENT = "#1f6feb"
TEXT = "#222"
SUCCESS = "#107e3e"
WARN = "#b76e00"
ERROR = "#c92a2a"

# Ensure directories exist
os.makedirs(LOG_BASE_DIR, exist_ok=True)
os.makedirs(BASE_DIR, exist_ok=True)

# ---------------- Utility functions ----------------
def safe_load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def safe_write_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print("Erro gravar JSON:", e)
        return False

def tail_file(path, lines=200):
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            end = f.tell()
            size = 1024
            data = b""
            while end > 0 and lines > 0:
                if end - size < 0:
                    size = end
                    f.seek(0)
                else:
                    f.seek(end - size)
                chunk = f.read(size)
                data = chunk + data
                end -= size
                # count lines
                lines_count = data.count(b"\n")
                if lines_count > lines:
                    break
            text = data.decode(errors="ignore").splitlines()
            return text[-lines:]
    except Exception:
        return []

def download_config(remote_url=CONFIG_URL, save_to=CONFIG_CACHE, timeout=10):
    try:
        url = f"{remote_url}?nocache={random.randint(1000,999999)}"
        req = urllib.request.urlopen(url, timeout=timeout)
        if req.status == 200:
            content = req.read().decode()
            cfg = json.loads(content)
            safe_write_json(save_to, cfg)
            return cfg
    except Exception as e:
        print("Erro download config:", e)
    return None

def open_folder(path):
    try:
        os.startfile(path)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir a pasta: {e}")

# --------- Process execution (keep behavior similar to launcher) ----------
def executar_arquivo(path):
    """
    Executa arquivo (bat/cmd/ps1/exe). Abre nova janela para .bat/.cmd/.ps1,
    e executa silenciosamente para exe.
    Retorna (Popen obj or None).
    """
    if not os.path.exists(path):
        messagebox.showerror("Erro", f"Arquivo não encontrado:\n{path}")
        return None
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext in (".bat", ".cmd"):
            flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            proc = subprocess.Popen(["cmd.exe", "/c", path], cwd=os.path.dirname(path), creationflags=flags)
            return proc
        elif ext == ".ps1":
            flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            cmdline = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', path]
            proc = subprocess.Popen(cmdline, cwd=os.path.dirname(path), creationflags=flags)
            return proc
        else:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            proc = subprocess.Popen([path], cwd=os.path.dirname(path), creationflags=flags)
            return proc
    except Exception as e:
        messagebox.showerror("Erro ao executar", str(e))
        return None

# ------------- Service control (BaseService) -------------
def service_action(action):
    """
    action: 'start' or 'stop' or 'status'
    Uses sc start/stop and sc query. Requires permissions.
    """
    try:
        if action == "start":
            res = subprocess.run(["sc", "start", "BaseService"], capture_output=True, text=True)
            return res.returncode, res.stdout + res.stderr
        if action == "stop":
            res = subprocess.run(["sc", "stop", "BaseService"], capture_output=True, text=True)
            return res.returncode, res.stdout + res.stderr
        if action == "status":
            res = subprocess.run(["sc", "query", "BaseService"], capture_output=True, text=True)
            return res.returncode, res.stdout + res.stderr
    except Exception as e:
        return 1, str(e)

# ------------------ GUI -------------------
class LauncherPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Painel MonitoramentoBKP")
        self.root.geometry("980x700")
        self.root.configure(bg=BG)

        # load cached config/version
        self.config = safe_load_json(CONFIG_CACHE, default={"versao":"0.0.0","executar":[]})
        self.versao_local = safe_load_json(VERSION_FILE, default={"versao":"0.0.0","tipo":"CX1"})
        self.selected_script = None
        self.build_ui()
        self.start_auto_tasks()

    def build_ui(self):
        # Header
        header = Frame(self.root, bg=BG)
        header.pack(fill=X, padx=12, pady=10)
        Label(header, text="MonitoramentoBKP — Painel", font=("Segoe UI", 18, "bold"), bg=BG, fg=ACCENT).pack(side=LEFT)
        self.lbl_status_small = Label(header, text="", bg=BG, fg=TEXT)
        self.lbl_status_small.pack(side=RIGHT)

        # Tabs
        nb = ttk.Notebook(self.root)
        nb.pack(fill=BOTH, expand=True, padx=12, pady=(0,12))

        # Tab1 - Status Geral
        self.tab_status = Frame(nb, bg=BG)
        nb.add(self.tab_status, text="Status Geral")

        # Tab2 - Configuração
        self.tab_config = Frame(nb, bg=BG)
        nb.add(self.tab_config, text="Configuração")

        # Tab3 - Logs
        self.tab_logs = Frame(nb, bg=BG)
        nb.add(self.tab_logs, text="Logs")

        # Tab4 - Controle Manual
        self.tab_control = Frame(nb, bg=BG)
        nb.add(self.tab_control, text="Controle Manual")

        # Build each tab
        self.build_tab_status()
        self.build_tab_config()
        self.build_tab_logs()
        self.build_tab_control()

    # ---------------- Tab: Status Geral ----------------
    def build_tab_status(self):
        t = self.tab_status
        # top cards
        cards = Frame(t, bg=BG)
        cards.pack(fill=X, padx=12, pady=8)

        self.card_vars = {
            "filial": StringVar(value=self.versao_local.get("filial", "")),
            "terminal": StringVar(value=self.versao_local.get("tipo", "CX1")),
            "versao": StringVar(value=self.versao_local.get("versao", "0.0.0")),
            "service": StringVar(value="Desconhecido"),
            "ultimo_backup": StringVar(value="—"),
            "proxima_validacao": StringVar(value="—"),
            "ultima_comunicacao": StringVar(value="—")
        }

        def make_card(parent, title, var, width=26):
            f = Frame(parent, bg=CARD, bd=1, relief="flat")
            f.pack(side=LEFT, padx=8, pady=6)
            Label(f, text=title, font=("Segoe UI", 10), bg=CARD, fg="#666").pack(anchor="w", padx=10, pady=(8,0))
            Label(f, textvariable=var, font=("Segoe UI", 12, "bold"), bg=CARD, fg=TEXT).pack(anchor="w", padx=10, pady=(4,12))
            return f

        make_card(cards, "🏬 Filial", self.card_vars["filial"])
        make_card(cards, "💻 Terminal", self.card_vars["terminal"])
        make_card(cards, "🧩 Versão atual", self.card_vars["versao"])
        make_card(cards, "⚙️ Serviço BaseService", self.card_vars["service"])
        make_card(cards, "🕒 Último backup", self.card_vars["ultimo_backup"])
        make_card(cards, "⏰ Próxima validação", self.card_vars["proxima_validacao"])
        make_card(cards, "🌐 Última comunicação remota", self.card_vars["ultima_comunicacao"])

        # Buttons
        btns = Frame(t, bg=BG)
        btns.pack(fill=X, padx=12, pady=6)
        Button(btns, text="▶️ Iniciar Serviço", command=self.on_start_service, width=18).pack(side=LEFT, padx=6)
        Button(btns, text="⏹️ Parar Serviço", command=self.on_stop_service, width=18).pack(side=LEFT, padx=6)
        Button(btns, text="🔄 Rodar validação agora", command=self.on_run_valida, width=20).pack(side=LEFT, padx=6)
        Button(btns, text="🧰 Abrir pasta de logs", command=lambda: open_folder(LOG_BASE_DIR), width=18).pack(side=LEFT, padx=6)
        Button(btns, text="🌐 Baixar config remoto", command=self.on_download_config, width=18).pack(side=LEFT, padx=6)

        # status area text
        self.status_text = Text(t, height=8, bg=CARD, fg=TEXT, bd=0)
        self.status_text.pack(fill=BOTH, expand=False, padx=12, pady=(8,12))
        self.status_text.insert(END, "Painel iniciado...\n")
        self.status_text.configure(state="disabled")

    # ---------------- Tab: Configuração ----------------
    def build_tab_config(self):
        t = self.tab_config
        # show current versao.config and allow editing 'tipo' and 'filial'
        frame = Frame(t, bg=BG)
        frame.pack(fill=X, padx=12, pady=12)

        Label(frame, text="versao.config (integração)", bg=BG, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        sub = Frame(frame, bg=BG)
        sub.pack(fill=X, pady=6)

        Label(sub, text="Tipo (SERVIDOR / CX1 / CX2):", bg=BG).grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.entry_tipo = StringVar(value=self.versao_local.get("tipo", "CX1"))
        Entry(sub, textvariable=self.entry_tipo, width=20).grid(row=0, column=1, padx=4, pady=4)

        Label(sub, text="Filial (ID):", bg=BG).grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.entry_filial = StringVar(value=self.versao_local.get("filial", ""))
        Entry(sub, textvariable=self.entry_filial, width=50).grid(row=1, column=1, padx=4, pady=4)

        Label(sub, text="Versão local:", bg=BG).grid(row=2, column=0, sticky="w", padx=4, pady=4)
        self.entry_versao = StringVar(value=self.versao_local.get("versao", "0.0.0"))
        Entry(sub, textvariable=self.entry_versao, width=20).grid(row=2, column=1, padx=4, pady=4)

        Button(frame, text="💾 Salvar em versao.config", command=self.on_save_version).pack(anchor="w", pady=8)

        # Show remote config (cached)
        Label(frame, text="Config remoto (cache)", bg=BG, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8,0))
        self.config_preview = Text(frame, height=12, bg=CARD, fg=TEXT, bd=0)
        self.config_preview.pack(fill=BOTH, padx=4, pady=6)
        self.reload_config_preview()

    def reload_config_preview(self):
        cfg = safe_load_json(CONFIG_CACHE, default={})
        self.config = cfg
        self.config_preview.configure(state="normal")
        self.config_preview.delete(1.0, END)
        pretty = json.dumps(cfg, indent=2, ensure_ascii=False)
        self.config_preview.insert(END, pretty)
        self.config_preview.configure(state="disabled")

    # ---------------- Tab: Logs ----------------
    def build_tab_logs(self):
        t = self.tab_logs
        top = Frame(t, bg=BG)
        top.pack(fill=X, padx=12, pady=8)
        Button(top, text="🔍 Atualizar manualmente", command=self.refresh_log).pack(side=LEFT, padx=6)
        Button(top, text="🧹 Limpar log (apaga arquivo)", command=self.clear_log).pack(side=LEFT, padx=6)
        Button(top, text="📂 Abrir pasta de logs", command=lambda: open_folder(LOG_BASE_DIR)).pack(side=LEFT, padx=6)

        # log text area with scrollbar
        area = Frame(t, bg=BG)
        area.pack(fill=BOTH, expand=True, padx=12, pady=8)
        self.log_text = Text(area, wrap="none", bg="#0b1220", fg="#e6eef8", font=("Consolas", 10), padx=8, pady=8)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        scr = Scrollbar(area, command=self.log_text.yview)
        scr.pack(side=RIGHT, fill=Y)
        self.log_text.config(yscrollcommand=scr.set)
        self.refresh_log()

    def refresh_log(self):
        lines = tail_file(LAUNCHER_LOG, LOG_TAIL_LINES)
        if not lines:
            self.log_text.configure(state="normal")
            self.log_text.delete(1.0, END)
            self.log_text.insert(END, "(arquivo de log vazio ou inexistente)\n")
            self.log_text.configure(state="disabled")
            return
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, END)
        for ln in lines:
            # colorize by prefix emoji
            text = ln + "\n"
            self.log_text.insert(END, text)
        self.log_text.configure(state="disabled")

    def clear_log(self):
        if messagebox.askyesno("Confirmar", "Deseja apagar o arquivo launcher.log?"):
            try:
                open(LAUNCHER_LOG, "w").close()
                self.refresh_log()
                messagebox.showinfo("Ok", "Arquivo launcher.log limpo.")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível limpar o log: {e}")

    # ---------------- Tab: Controle Manual ----------------
    def build_tab_control(self):
        t = self.tab_control
        top = Frame(t, bg=BG)
        top.pack(fill=X, padx=12, pady=8)
        Button(top, text="🔄 Recarregar config (remote)", command=self.on_download_config).pack(side=LEFT, padx=6)
        Button(top, text="🔁 Recarregar lista", command=self.reload_exec_list).pack(side=LEFT, padx=6)

        mid = Frame(t, bg=BG)
        mid.pack(fill=BOTH, expand=True, padx=12, pady=8)

        left = Frame(mid, bg=BG)
        left.pack(side=LEFT, fill=Y, padx=(0,8))
        Label(left, text="Scripts/configurados:", bg=BG).pack(anchor="w")
        self.listbox = Listbox(left, width=45, height=20)
        self.listbox.pack(fill=Y, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select_script)

        right = Frame(mid, bg=BG)
        right.pack(side=LEFT, fill=BOTH, expand=True)
        Label(right, text="Detalhes / Execução", bg=BG).pack(anchor="w")
        self.details = Text(right, height=12, bg=CARD)
        self.details.pack(fill=BOTH, expand=True)
        btn_frame = Frame(right, bg=BG)
        btn_frame.pack(fill=X, pady=6)
        Button(btn_frame, text="▶️ Executar agora", command=self.on_execute_selected).pack(side=LEFT, padx=6)
        Button(btn_frame, text="📂 Abrir pasta do script", command=self.on_open_script_folder).pack(side=LEFT, padx=6)

        self.reload_exec_list()

    def reload_exec_list(self):
        cfg = safe_load_json(CONFIG_CACHE, default={})
        executar = cfg.get("executar", [])
        self.listbox.delete(0, END)
        for item in executar:
            nome = item.get("nome", "desconhecido")
            ativo = item.get("ativo", True)
            tag = f"{nome} {'(ativo)' if ativo else '(inativo)'}"
            self.listbox.insert(END, tag)
        self.config = cfg

    def on_select_script(self, ev=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        item = self.config.get("executar", [])[idx]
        pretty = json.dumps(item, indent=2, ensure_ascii=False)
        self.selected_script = item
        self.details.configure(state="normal")
        self.details.delete(1.0, END)
        self.details.insert(END, pretty)
        self.details.configure(state="disabled")

    def on_execute_selected(self):
        item = self.selected_script
        if not item:
            messagebox.showwarning("Atenção", "Selecione um script na lista.")
            return
        path = self.resolve_executable_path(item)
        if not path or not os.path.exists(path):
            messagebox.showerror("Erro", f"Arquivo não encontrado: {path}")
            return

        def run_and_capture():
            proc = executar_arquivo(path)
            if not proc:
                self.append_status(f"Falha ao iniciar {path}")
                return
            self.append_status(f"Iniciado {item.get('nome')} (PID {getattr(proc, 'pid', '')}) — aguardando término...")
            try:
                proc.wait(timeout=300)  # espera até 5min
                self.append_status(f"✅ {item.get('nome')} finalizou (returncode {proc.returncode})")
            except subprocess.TimeoutExpired:
                self.append_status(f"⏳ Tempo limite. Processo continua em execução (PID {proc.pid}).")

        threading.Thread(target=run_and_capture, daemon=True).start()

    def on_open_script_folder(self):
        item = self.selected_script
        if not item:
            return
        path = self.resolve_executable_path(item)
        if path and os.path.exists(path):
            open_folder(os.path.dirname(path))

    # ---------------- Actions ----------------
    def on_start_service(self):
        def job():
            code, out = service_action("start")
            if code == 0:
                messagebox.showinfo("Serviço", "Comando de start enviado com sucesso.")
            else:
                messagebox.showwarning("Serviço", f"Resultado: {out}")
            self.update_service_status()
        threading.Thread(target=job, daemon=True).start()

    def on_stop_service(self):
        def job():
            code, out = service_action("stop")
            if code == 0:
                messagebox.showinfo("Serviço", "Comando de stop enviado com sucesso.")
            else:
                messagebox.showwarning("Serviço", f"Resultado: {out}")
            self.update_service_status()
        threading.Thread(target=job, daemon=True).start()

    def on_run_valida(self):
        # run valida_bkp.exe in BASE_DIR
        path = os.path.join(BASE_DIR, "valida_bkp.exe")
        if not os.path.exists(path):
            messagebox.showerror("Erro", "valida_bkp.exe não encontrado.")
            return
        def job():
            proc = executar_arquivo(path)
            if proc:
                self.append_status("valida_bkp iniciado (aguardando término)...")
                proc.wait()
                self.append_status(f"valida_bkp finalizado (returncode {proc.returncode})")
        threading.Thread(target=job, daemon=True).start()

    def on_download_config(self):
        def job():
            cfg = download_config()
            if cfg:
                self.append_status("Config remoto baixado e salvo em config_cache.json")
                self.reload_config_preview()
                self.reload_exec_list()
                # update last communication time and card values
                self.card_vars["ultima_comunicacao"].set(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            else:
                self.append_status("Falha ao baixar config remoto.")
        threading.Thread(target=job, daemon=True).start()

    def on_save_version(self):
        v = self.entry_versao.get().strip()
        t = self.entry_tipo.get().strip().upper()
        filial = self.entry_filial.get().strip()
        if not v:
            messagebox.showwarning("Atenção", "Informe a versão.")
            return
        data = {"versao": v, "tipo": t, "filial": filial}
        ok = safe_write_json(VERSION_FILE, data)
        if ok:
            messagebox.showinfo("Ok", "versao.config atualizada.")
            self.versao_local = data
            self.card_vars["versao"].set(v)
            self.card_vars["terminal"].set(t)
            self.card_vars["filial"].set(filial)
        else:
            messagebox.showerror("Erro", "Falha ao gravar versao.config.")

    # ---------------- Helpers ----------------
    def append_status(self, msg):
        ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.status_text.configure(state="normal")
        self.status_text.insert(END, f"[{ts}] {msg}\n")
        self.status_text.see(END)
        self.status_text.configure(state="disabled")

    def update_service_status(self):
        code, out = service_action("status")
        state = "Desconhecido"
        if code == 0:
            if "RUNNING" in out or "RUNNING" in out.upper():
                state = "🟢 Em execução"
            elif "STOPPED" in out or "STOPPED" in out.upper():
                state = "🔴 Parado"
            else:
                state = "🟡 " + out.splitlines()[0][:50]
        else:
            state = "⚠️ Erro"
        self.card_vars["service"].set(state)

    def resolve_executable_path(self, exe_info):
        nome = exe_info.get("nome")
        local = exe_info.get("local", BASE_DIR)
        # if local is a path to a folder
        if os.path.isdir(local):
            return os.path.join(local, nome)
        # if local looks like absolute file path
        if os.path.isabs(local) and os.path.splitext(local)[1]:
            return local
        # otherwise join
        return os.path.join(BASE_DIR, nome)

    # ---------------- Auto tasks ----------------
    def start_auto_tasks(self):
        # update UI with cached values
        self.card_vars["versao"].set(self.versao_local.get("versao", "0.0.0"))
        self.card_vars["terminal"].set(self.versao_local.get("tipo", "CX1"))
        self.card_vars["filial"].set(self.versao_local.get("filial", ""))
        self.update_service_status()
        self.append_status("Painel iniciado")
        # start log auto-refresh
        self._stop_flag = False
        self._log_thread = threading.Thread(target=self.auto_refresh_log, daemon=True)
        self._log_thread.start()
        # auto config refresh (background)
        self._cfg_thread = threading.Thread(target=self.auto_refresh_config_cache, daemon=True)
        self._cfg_thread.start()

    def auto_refresh_log(self):
        while True:
            try:
                self.refresh_log()
            except Exception:
                pass
            time.sleep(AUTO_REFRESH_LOG_SECONDS)

    def auto_refresh_config_cache(self):
        while True:
            try:
                # try to read cache (if exists)
                cfg = safe_load_json(CONFIG_CACHE, default=None)
                if cfg:
                    # update some card values based on config: next validation (if valida present)
                    executar = cfg.get("executar", [])
                    # attempt to extract valida schedule if present
                    for item in executar:
                        if item.get("nome", "").lower().startswith("valida"):
                            horario = item.get("horario")
                            if horario:
                                if isinstance(horario, list):
                                    next_h = horario[0]
                                else:
                                    next_h = horario
                                self.card_vars["proxima_validacao"].set(next_h if next_h else "—")
                # update timestamp card
                # self.card_vars["ultima_comunicacao"].set(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            except Exception:
                pass
            time.sleep(CHECK_CONFIG_INTERVAL)

# ------------------ Run UI ------------------
def main():
    root = Tk()
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except:
        pass
    app = LauncherPanel(root)
    root.mainloop()

if __name__ == "__main__":
    main()
