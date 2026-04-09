# Documentação de Arquitetura do Projeto RSSF

Esta documentação descreve a arquitetura do projeto de Rede de Sensores Sem Fio (RSSF) com base nos arquivos extraídos. O projeto monitora as temperaturas usando sensores DS18B20 e transmite os dados via LoRa para um dispositivo receptor que, por sua vez, envia para um servidor centralizado hospedado em uma API (Flask + MySQL).

---

## 1. Estrutura de Diretórios
A nova estrutura do projeto foi padronizada da seguinte forma:

```text
rssf/
├── firmware/                        # Todo código embarcado (ESP32)
│   ├── receptor/                    # Nó receptor (Conectado via LoRa e WiFi)
│   └── transmissor/                 # Nó transmissor (Coleta dados de sensores)
├── backend/                         # API Web construída em Python (Flask) e MySQL
│   ├── app.py                       # Ponto de entrada da aplicação
│   ├── requirements.txt             # Dependências de bibliotecas
│   ├── config.py                    # Configurações do Banco de Dados
│   ├── routes/                      # Rotas da API e Endpoints HTTP
│   ├── models/                      # Camada de Regra de Negócio e persistência (MySQL)
│   └── database/                    # Scripts SQL para inicializar ou resetar as tabelas
├── site/                            # Pasta para o frontend (página HTML/CSS/JS)
└── docs/                            # Documentação do projeto (este arquivo e outros)
```

---

## 2. Firmware (Nós da Rede)

### 2.1. Nó Transmissor (Coleta)
- **Microcontrolador**: Sugerido ESP32
- **Módulo RF**: LoRa E220 (TX_PIN = 17, RX_PIN = 16)
- **Sensores de Temperatura**: Protocolo OneWire (Pino 15), gerencia 6 sensores DS18B20, que possuem endereços HEX pré-definidos (S1 a S6).
- **Parâmetros de Comunicação LoRa**: 
  - `NODE_ADDRESS`: 0x0002
  - `CHANNEL`: 0x0F (Canal 15)
  - `TRANSMISSION_MODE`: Fixed Transmission
- **Consumo de Energia**: Configurado `Deep Sleep` de 30 minutos (1.800.000 ms), acordando periodicamente para fazer as medições, enviá-las e dormir novamente.

### 2.2. Nó Receptor (Gateway LoRa / Wi-Fi)
- **Modo de Operação**: `MODE_2_WOR_RECEIVER` (Wake on Radio - Receptor).
- **Comunicação Web**: 
  - Conecta-se à rede WiFi "LSP/UEMA".
  - Fica aguardando novas mensagens do transmissor.
  - Formata as 6 leituras de temperatura (S1-S6) e a potência do sinal (`RSSI`) num objeto JSON.
  - Realiza um _POST_ via HTTP (`http://172.17.32.196:5000/api/salvar_dados`) redirecionado para a API local na rede.

---

## 3. Backend (API de Acesso a Dados)

### 3.1. Principais Módulos
- **Flask**: Criação do serviço e roteamento da rede (porta 5000).
- **MySQL Connector Python**: Gerencia a conexão com o banco de dados MySQL para armazenamento dos pacotes criados pelo sistema.

### 3.2. Arquitetura Modular
- `config.py`: Local para variáveis do banco (Host `localhost`, Database e senhas).
- `models/medicao.py`: Encapsula a lógica da camada de banco, responsável por abrir conexões, rodar a instrução `INSERT INTO` convertendo a string de JSON do receptor.
- `routes/medicoes.py`: Registra uma rota com controle de erro (`POST /api/salvar_dados`).
- `app.py`: Realiza apenas a inicialização dos *blueprints* da aplicação Flask usando importações limpas.

### 3.3. Banco de Dados MySQL (`database/schema.sql`)
O banco principal chamado `rssf` armazena os dados sob demanda de tempo na tabela `medicoes` utilizando a base:
1. `id` INT (Chave Primária)
2. `data_hora` TIMESTAMP (Data de recebimento no servidor)
3. `sensor_id` INT (Endereço do remetente / senderAddress)
4. `temp_ds1` até `temp_ds6` (Temperaturas lidas em ponto flutuante Float)
5. `rssi` (Valor Float representando a força do sinal na interconexão LoRa)

---

## 4. Frontend (Sistema Visual)
- Fica hospedado no diretório `site/`.
- Estruturado em divisões modulares (`css`, `js`, `index.html`) para futuramente consumir dados da API hospedada no _Backend_ (por exemplo, criando tabelas de monitoramento em tempo real ou gráficos dos 6 sensores conectados a um painel dashboard).
