# AhGora Automation

Automação de ponto eletrônico no SAP SuccessFactors (Universo On) com Playwright (Python).

Registra solicitações de abono (Teletrabalho) automaticamente — um dia específico ou o mês inteiro, pulando dias já marcados e fins de semana.

## Segurança

- **Usuário e senha nunca passam pelo terminal** — você digita apenas no navegador.
- A sessão fica em `auth/storage.json` (cookies), que está no `.gitignore`.
- Não commite `auth/` no Git.

---

## Instalação (primeira vez)

Abra o PowerShell na pasta do projeto e rode o setup:

```powershell
cd C:\dev\AhGoraAutomation
.\setup.bat
```

Isso vai:

1. Criar o ambiente virtual em `.venv`
2. Instalar dependências do `requirements.txt`
3. Baixar o Chromium do Playwright

Alternativa manual:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
$env:PLAYWRIGHT_BROWSERS_PATH="0"; .venv\Scripts\playwright install chromium
```

---

## Passo a passo de uso

### 1. Fazer login

```powershell
.\login.bat
```

- O Chromium abre na página da Universo On.
- Faça login normalmente **no navegador** (usuário/senha só lá).
- Ao entrar na home, a sessão é salva automaticamente em `auth/storage.json` e o navegador fecha.

Refaça o login sempre que aparecer erro de "popup timeout" ou "Ajuste de Ponto" (sessão expirada).

### 2. Bater ponto de um único dia

Dia de hoje, 09:00–18:00, Teletrabalho:

```powershell
.\bater_ponto.bat
```

Dia específico:

```powershell
.\bater_ponto.bat --data 2026-08-11
```

Com horário customizado:

```powershell
.\bater_ponto.bat --data 2026-08-11 --hora-inicio 08:30 --hora-fim 17:30
```

### 3. Bater ponto de um mês inteiro

O script pega todos os dias úteis do mês que ainda **não têm** ícone (estrela ou balão amarelo) e envia a solicitação para cada um.

Sempre confira antes com `--dry-run` (não envia nada, só lista):

```powershell
.\bater_mes.bat --mes 2026-08 --dry-run
```

Saída de exemplo:

```
Dias ja marcados (com icone): [(1, 'star'), (2, 'star'), (6, 'mode_comment')]
Dias livres (sem icone): [4, 5, 10, 11, ...]
Dias uteis a processar: [4, 5, 10, 11, 12, 13, 14, ...]
```

Se estiver correto, rode sem `--dry-run`:

```powershell
.\bater_mes.bat --mes 2026-08
```

### 4. Filtros úteis por dia

Só a partir de um dia:

```powershell
.\bater_mes.bat --mes 2026-08 --min-dia 15
```

Faixa de dias:

```powershell
.\bater_mes.bat --mes 2026-08 --min-dia 10 --max-dia 20
```

---

## Todos os parâmetros

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `--data` | hoje | (Só `bater_ponto`) Data da solicitação `YYYY-MM-DD` |
| `--mes` | — | (Só `bater_mes`) Mês alvo `YYYY-MM` (obrigatório) |
| `--min-dia` | 1 | (Só `bater_mes`) Ignora dias anteriores |
| `--max-dia` | 31 | (Só `bater_mes`) Ignora dias posteriores |
| `--dry-run` | off | (Só `bater_mes`) Só lista, não envia |
| `--hora-inicio` | 09:00 | Hora inicial |
| `--hora-fim` | 18:00 | Hora final |
| `--motivo` | Teletrabalho | Motivo do abono |
| `--mensagem` | Teletrabalho/HomeOffice | Texto da solicitação |
| `--headless` | off | Executa sem abrir janela |

---

## Como o script detecta dias já batidos

Cada dia no calendário do Ajuste de Ponto pode ter um dos indicadores:

| Ícone | Significado | Considerado batido? |
|-------|-------------|---------------------|
| `star` (roxa) | Ajuste aprovado | Sim |
| `mode_comment` (balão amarelo) | Solicitação pendente | Sim |
| (nenhum) | Livre | Não |

O `bater_mes.bat` pula qualquer dia com ícone e também fins de semana (sáb/dom).

---

## Estrutura do projeto

```
AhGoraAutomation/
├── auth/
│   └── storage.json          # sessão salva (ignorada pelo git)
├── scripts/
│   ├── login.py              # login manual e salvamento da sessão
│   ├── bater_ponto.py        # registra abono em um dia
│   ├── bater_mes.py          # registra abono em um mês inteiro
│   └── recorded.py           # fluxo bruto do Playwright codegen
├── login.bat                 # atalho: login
├── bater_ponto.bat           # atalho: um dia
├── bater_mes.bat             # atalho: mês inteiro
├── setup.bat                 # instala tudo
├── requirements.txt
└── README.md
```

---

## Gravar de novo (se a plataforma mudar)

Se o AhGora mudar botões/campos e o script quebrar, grave o fluxo novamente:

```powershell
.venv\Scripts\playwright.exe codegen --load-storage=auth/storage.json --target python -o scripts\recorded.py "https://hcm19.sapsf.com/sf/home?bplte_company=universoon"
```

Execute o fluxo no navegador → o código Python é salvo em `scripts/recorded.py`. Compare com `bater_ponto.py` e ajuste os seletores.

---

## Solução de problemas

**`Executable doesn't exist at ...\ms-playwright\...\chrome.exe`**  
Rode `.\setup.bat` novamente. Os `.bat` já forçam o browser a ficar dentro do `.venv`.

**`Timeout ... waiting for event "popup"`**  
Sessão expirou. Rode `.\login.bat`.

**`ModuleNotFoundError: No module named 'playwright'`**  
Você chamou `python scripts/...` com o Python global. Use os `.bat` ou:

```powershell
.venv\Scripts\python.exe scripts\bater_ponto.py
```

**Script marca dias que já estavam batidos**  
Verifique o estado do dia no site. Se tiver algum ícone novo que não é `star` nem `mode_comment`, me avise para adicionar à detecção.
