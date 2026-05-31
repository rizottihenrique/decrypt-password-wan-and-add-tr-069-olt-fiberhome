# Script de migração e apontamento massivo de TR-069 - OLT Fiberhome AN5000/6000 Series

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FiberHome](https://img.shields.io/badge/FiberHome-009A44?style=for-the-badge&logoColor=white)
![Network Automation](https://img.shields.io/badge/Network_Automation-0057D9?style=for-the-badge)

Este script automatizado em Python foi desenvolvido especificamente para cenários de migração, auditoria e gerência centralizada de provedores de internet (ISPs). O objetivo principal da ferramenta é **automatizar o apontamento e a ativação do protocolo TR-069 (ACS)** em milhares de ONTs simultaneamente através da CLI da OLT.

Para que o apontamento do TR-069 funcione perfeitamente sem intervenção manual, o script processa os arquivos de configuração em lote e resolve três grandes gargalos de uma só vez:
1. **Ativação da WAN TR-069 (Dual Stack):** Altera o perfil da WAN de `mode inter` para `mode tr069_int` e força o provisionamento em IPv4/IPv6 (`both`) via `dhcpv6`.
2. **Desofuscação de Senhas PPPoE:** Quebra a criptografia estática nativa do firmware (`key:VALOR`), inserindo as senhas reais em texto claro para que a migração não derrube a autenticação dos clientes.
3. **Divisão de Contexto da CLI (Context-Aware):** Separa os comandos em blocos distintos de execução (WAN e Gerência Remota), respeitando a árvore de diretórios nativa da OLT.

---

## 1. Funcionamento e Arquitetura do Script

O script divide o arquivo final (`output.txt`) em duas etapas lógicas fundamentais para que você possa copiar e colar no terminal da OLT sem erros de sintaxe ou contexto:

### Bloco 1: Ajuste de WAN e Conectividade (Diretório: `gepon/onu/lan`)
Cada ONU possui um par de comandos sequenciais. O script intercepta essas linhas, aplica as correções de protocolo, traduz a senha, insere o comando de validação (`apply wancfg`) e pula uma linha para o próximo equipamento.
* **Modificação do Modo:** Substitui `mode inter` por `mode tr069_int`.
* **Upgrade de IP-Stack:** Altera a pilha de rede antiga (`ipv4` / `slaac`) para o padrão recomendado de transição: Dual Stack (`both`) com atribuição dinâmica via `dhcpv6`.

### Bloco 2: Apontamento Remoto do Servidor ACS (Diretório: `gepon/onu`)
Como o comando de gerenciamento remoto pertence a outro nível da CLI, o script mapeia dinamicamente todos os IDs de **Slot, Pon e ONU** processados no Bloco 1 e, no final do arquivo, gera de forma isolada a lista de comandos para direcionar os equipamentos até o servidor TR-069 do provedor.

---

## 2. Como o Script Funciona por Baixo dos Panos

### A Lógica da Cifra (Espelhamento ASCII)
Durante os testes empíricos em bancada utilizando senhas conhecidas (como `aaaaaa` e o alfabeto completo), descobriu-se que o firmware da OLT não utiliza uma criptografia complexa (como MD5 ou AES), mas sim uma **Cifra de Substituição por Espelhamento** baseada na tabela ASCII padrão.

A regra matemática exata aplicada pelo firmware para mascarar cada caractere é:

$$\text{Valor ASCII do Caractere Mascarado} = 158 - \text{Valor ASCII da Senha Real}$$

Para reverter a senha e descobrir o texto claro, o script faz a operação inversa:

$$\text{Valor ASCII da Senha Real} = 158 - \text{Valor ASCII do Caractere Mascarado}$$

#### Exemplo Prático de Conversão:
* A letra **`a`** possui o valor ASCII **97**.
* Aplicando a fórmula: $158 - 97 = 61$.
* O valor **61** na tabela ASCII corresponde ao caractere **`=`**.
* Portanto, se a senha gravada for `aaaaaa`, o comando na OLT exibirá `key:======`.

---

## 3. Otimizações de Performance (Processamento em Lote)

O script foi desenhado especificamente para ambientes de provedores de internet (ISPs) que lidam com **milhares de ONTs simultaneamente**. Para garantir velocidade máxima e consumo mínimo de hardware, foram aplicadas duas técnicas avançadas:

1. **Processamento em Stream (Linha por Linha):** O script não carrega o arquivo `.txt` inteiro na memória RAM. Ele lê, processa e escreve uma linha por vez. Isso significa que você pode processar um arquivo de configuração de 2GB contendo milhões de ONTs utilizando praticamente 0% de memória RAM.
2. **Tabela de Tradução Nativa (`str.maketrans`):** Em vez de fazer loops em Python caractere por caractere (o que seria lento), o script pré-calcula a tabela de reversão de todos os caracteres visíveis e utiliza a função `.translate()`. Essa função executa a substituição das strings diretamente em **nível de linguagem C** (mecanismo interno do Python), tornando a conversão instantânea.

---

## 4. Pré-requisitos

* Python 3.6 ou superior instalado no sistema.
* Não é necessária a instalação de nenhuma biblioteca de terceiros (o script utiliza apenas módulos nativos: `re` e `sys`).

---

## 5. Como Utilizar

1. Extraia o relatório ou o arquivo de texto contendo as linhas de comando da sua OLT.
2. Salve esse arquivo com o nome de **`input.txt`** na mesma pasta onde o script `decodificador.py` está localizado.
3. Abra o seu terminal (Prompt de Comando ou PowerShell) na pasta do projeto e execute:

```bash
python decodificador.py
```

---
