import xml.etree.ElementTree as ET

# Pega o primeiro item da entrada
input_item = _items[0]
xml_content = input_item["json"].get('data')

lista_para_planilha = []

if xml_content:
    try:
        # Lê o XML ignorando namespaces complexos
        root = ET.fromstring(xml_content)
        base_url = "https://www.portalnomades.com/imovel/"

        # Encontra todas as listings ignorando o namespace com {*}
        listings = root.findall('.//{*}Listing')

        for listing in listings:
            try:
                # --- Funções Auxiliares (definidas aqui para usar o 'listing' atual) ---

                # Pega valor da tag, retorna padrão se vazio
                def get_val(tag_name, default="0"):
                    val = listing.findtext(f'.//{{*}}{tag_name}')
                    return str(val).strip() if val else default

                # Pega a primeira imagem disponível
                def get_image():
                    media_item = listing.find('.//{*}Media/{*}Item')
                    if media_item is not None:
                        # Tenta pegar texto interno ou atributo url
                        return media_item.text or media_item.get('url') or ""
                    return ""

                # --- EXTRAÇÃO DOS DADOS ---

                listing_id = get_val('ListingID', "")
                # Se não tiver ID, pula este item
                if not listing_id:
                    continue

                # 1. Define a Transação e Traduz (Passo crucial vir antes dos preços)
                raw_transacao = get_val('TransactionType', "Venda/Aluguel")
                mapa_traducao = {
                    "For Rent": "Aluguel",
                    "For Sale": "Venda",
                    "Sale": "Venda",
                    "Rent": "Aluguel"
                }
                transacao = mapa_traducao.get(raw_transacao, raw_transacao)

                # 2. Pega os dois preços possíveis do XML
                preco_locacao = get_val('RentalPrice', "0")
                preco_venda = get_val('ListPrice', "0")

                # 3. Lógica Condicional para definir o PREÇO ÚNICO
                # Se for Aluguel, usa o de locação. Caso contrário (Venda), usa o de venda.
                if transacao == "Aluguel":
                    valor_final_decidido = preco_locacao
                else:
                    valor_final_decidido = preco_venda


                # Dados Numéricos e Texto
                condominio = get_val('PropertyAdministrationFee', "0")
                iptu = get_val('YearlyTax', "0")
                area = get_val('LivingArea', "0")
                quartos = get_val('Bedrooms', "0")
                banheiros = get_val('Bathrooms', "0")
                suites = get_val('Suites', "0")
                vagas = get_val('Garage', "0")

                bairro = get_val('Neighborhood', "")
                cidade = get_val('City', "")
                uf = get_val('State', "")
                descricao = get_val('Description', "")

                # Título
                titulo_xml = get_val('Title', "")
                tipo_imovel = get_val('PropertyType', "Imóvel")


                # Monta Título se não existir
                if titulo_xml and len(titulo_xml) > 5:
                    titulo_final = titulo_xml
                else:
                    titulo_final = f"{tipo_imovel} para {transacao}, por R$ {valor_final_decidido} - {bairro} - {cidade}/{uf}"

                # --- CRIAÇÃO DO DICIONÁRIO FINAL ---
                # A ordem aqui não importa para o Python, mas as CHAVES devem ser idênticas às da Planilha
                imovel_dict = {
                    "id": listing_id,
                    "titulo": titulo_final,
                    "finalidade": transacao,
                    "bairro": bairro,
                    "valor_principal": valor_final_decidido,
                    "condominio": condominio,
                    "iptu": iptu,
                    "area": area,
                    "quartos": quartos,
                    "banheiros":banheiros,
                    "suites": suites,
                    "vagas": vagas,
                    "descricao": descricao,
                    "link": base_url + listing_id,
                    "imagem": get_image()
                }

                # Adiciona na lista de saída envelopado em "json"
                lista_para_planilha.append({"json": imovel_dict})

            except Exception as e:
                # Se der erro em um imóvel específico, apenas printa e continua para o próximo
                print(f"Erro ao processar imóvel ID {listing_id if 'listing_id' in locals() else 'desconhecido'}: {str(e)}")

    except Exception as e:
        print(f"Erro fatal ao ler o XML: {str(e)}")

# Retorna a lista completa para o próximo nó
return lista_para_planilha