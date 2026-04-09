# RSSF — Rede de Sensores Sem Fio

Sistema IoT para monitoramento de temperatura utilizando comunicação LoRa, com coleta de dados via ESP32, armazenamento em banco MySQL e visualização via frontend web.

> 🚧 Status: **Funcional mas incompleto** — infraestrutura de rede operacional, integração com frontend em andamento.

---

## Arquitetura

```
[Nó Transmissor ESP32]
        |
      LoRa
        |
[Nó Receptor ESP32] ──── HTTP POST ────> [API Flask] ──> [MySQL]
                                                              |
                                                        [Frontend Web]
                                                        (Vercel)
```

---

## Estrutura do Repositório

```
rssf/
├── firmware/
│   ├── receptor/src/main.cpp       # ESP32 receptor LoRa + envio HTTP
│   └── transmissor/src/main.cpp    # ESP32 nó sensor transmissor
│
├── backend/
│   ├── app.py                      # Entry point da API Flask
│   ├── config.py                   # Configurações (DB, servidor)
│   ├── requirements.txt            # Dependências Python
│   ├── routes/
│   │   └── medicoes.py             # Rotas da API
│   ├── models/
│   │   └── medicao.py              # Acesso ao banco de dados
│   └── database/
│       └── schema.sql              # Script de criação das tabelas
│
├── frontend/                       # Submodule → repo frontend (Vercel)
├── docs/
│   └── arquitetura.md
└── .gitmodules
```

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Firmware | ESP32 + PlatformIO / Arduino |
| Comunicação | LoRa E220 |
| Backend | Python + Flask |
| Banco de dados | MySQL |
| Frontend | (submodule) — deploy no Vercel |

---

## Pré-requisitos

- Python 3.8+
- MySQL rodando localmente
- PlatformIO ou Arduino IDE
- Git com suporte a submodules

---

## Como Rodar

### 1. Clonar o repositório (com submodule)

```bash
git clone --recurse-submodules https://github.com/ayrtonct/rssf.git
cd rssf
```

> Se já clonou sem o submodule:
> ```bash
> git submodule update --init --recursive
> ```

### 2. Configurar o banco de dados

```bash
mysql -u root -p < backend/database/schema.sql
```

### 3. Configurar variáveis de ambiente (opcional)

Crie um arquivo `.env` na pasta `backend/`:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=rssf
```

> Sem o `.env`, os valores padrão de `config.py` serão usados.

### 4. Instalar dependências e rodar a API

```bash
cd backend
pip install -r requirements.txt
python app.py
```

A API estará disponível em `http://localhost:5000`.

### 5. Firmware

Abra a pasta `firmware/receptor/` ou `firmware/transmissor/` no PlatformIO e faça o upload para o ESP32 correspondente.

---

## Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/salvar_dados` | Recebe medições do receptor |

**Exemplo de payload:**
```json
{
  "senderAddress": 2,
  "rssi": -14.5,
  "temp_ds1": 25.3,
  "temp_ds2": 25.1,
  "temp_ds3": 24.9,
  "temp_ds4": 25.0,
  "temp_ds5": 25.2,
  "temp_ds6": 25.4
}
```

---

## Roadmap

- [x] Comunicação LoRa entre nós
- [x] Recepção e envio HTTP para API
- [x] Armazenamento no banco MySQL
- [ ] Integração frontend ↔ API
- [ ] Autenticação na API
- [ ] Dashboard de monitoramento em tempo real

---

## Atualizar o submodule frontend

```bash
git submodule update --remote frontend
git add frontend
git commit -m "chore: atualiza submodule frontend"
```
