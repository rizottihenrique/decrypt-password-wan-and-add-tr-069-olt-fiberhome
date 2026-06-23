import re

# Tabela de decodificação da senha
tabela_traducao = str.maketrans({chr(i): chr(158 - i) for i in range(32, 127) if 0 <= (158 - i) <= 255})

def processar_lote_an6000_por_pon(arquivo_entrada, arquivo_saida):
    try:
        with open(arquivo_entrada, 'r', encoding='utf-8') as f_in, \
             open(arquivo_saida, 'w', encoding='utf-8') as f_out:
            
            f_out.write("! ==================================================\n")
            f_out.write("! MIGRACAO PARA FIBERHOME AN6000 (SEPARADO POR PON)\n")
            f_out.write("! ==================================================\n")

            pon_atual = None

            for linha in f_in:
                linha = linha.strip()
                
                # Ignora linhas em branco
                if not linha or linha.startswith('!'):
                    continue

                # 1. Identifica a entrada em uma nova interface PON
                if linha.startswith("interface pon"):
                    pon_atual = linha
                    # Adiciona uma quebra de linha antes para organizar visualmente os blocos
                    f_out.write(f"\n{pon_atual}\n")
                    continue
                
                # Se encontrarmos comandos de ONU antes de ter uma PON lida, ignoramos
                if not pon_atual:
                    continue

                # 2. Processa e ajusta a linha WAN principal
                if linha.startswith("onu wan-cfg") and "key:" in linha:
                    linha = re.sub(r'mode \S+', 'mode tr069-int', linha)
                    linha = linha.replace('vlanm tag', 'vlan tag')
                    
                    match_key = re.search(r'key:(\S+)', linha)
                    if match_key:
                        senha_cripto = match_key.group(1)
                        senha_real = senha_cripto.translate(tabela_traducao)
                        linha = linha.replace(f"key:{senha_cripto}", senha_real)
                    
                    f_out.write(linha + "\n")

                # 3. Processa a linha IPv6 e atrela o TR069 à mesma ONU
                elif linha.startswith("onu ipv6-wan-cfg"):
                    match = re.search(r'onu ipv6-wan-cfg\s+(\S+)', linha)
                    indice_onu = match.group(1) if match else "1"
                    
                    linha = linha.replace('ip-stack-mode ipv4', 'ip-stack-mode both')
                    linha = linha.replace('ipv6-src-type slaac', 'ipv6-src-type dhcpv6')
                    
                    if "ipv6-address" not in linha:
                        linha += " ipv6-address ::/0 ipv6-gateway :: ipv6-master-dns :: ipv6-slave-dns :: ipv6-static-prefix ::/0"

                    f_out.write(linha + "\n")
                    
                    # Injeta o TR-069 logo abaixo do IPv6
                    cmd_tr069 = f"onu remote-manage-cfg {indice_onu} tr069 enable acs-url http://tr069.acme.com.br:8088 acl-user admin acl-pswd acme@123 inform enable interval 59834 port 0 user Admin pswd acme@123\n"
                    f_out.write(cmd_tr069 + "\n")

        print(f"Sucesso! Script gerado preservando a hierarquia das interfaces PON em: {arquivo_saida}")
        
    except FileNotFoundError:
        print(f"Erro: O arquivo '{arquivo_entrada}' não foi encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    arquivo_input = "input.txt"
    arquivo_output = "output.txt"
    
    processar_lote_an6000_por_pon(arquivo_input, arquivo_output)
