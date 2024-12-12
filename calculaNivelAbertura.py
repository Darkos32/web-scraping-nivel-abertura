#bibliotecas
from calendar import Calendar
from csv import writer
from csv import DictReader
from datetime import date
from glob import glob
from re import search
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as CONST_EC
from selenium.webdriver.support.wait import WebDriverWait
from time import sleep

#defincição de constantes
CONST_MESES_DO_ANO = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12
}
CONST_URL_INICIAL = 'https://www.data.rio/search?groupIds=cbe84df2333a463b9d4e20aca5177936' #url em que o webCrawler se inicia
#CONST_URL_INICIAL = 'https://www.data.rio/datasets/7a0b22723c5a458faaae79f046163504/about' #url em que o webCrawler se inicia
#elementos para criação do browser simulado
CONST_SERVISE = Service()
CONST_OPTIONS = webdriver.ChromeOptions()
CONST_BROWSER = webdriver.Chrome(service=CONST_SERVISE,options=CONST_OPTIONS)
#
CONST_MESES_ANO_REGEX ='\b([Jj]aneiro|[Ff]evereiro|[Mm]arço|[Aa]bril|[Mm]aio|[Jj]unho|[Jj]ulho|[Aa]gosto|[Ss]etembro|[Oo]utubro|[Nn]ovembro|[Dd]ezembro)\b'

# converte uma lista de listas em uma lista única
def achataLista(lista):
    achatada = []
    for l in  lista:
        achatada+=l
    return achatada
#Converte a string de uma lista para uma lista
def listaStringParaLista(lista):
    return lista.replace('[','').replace(']','').replace("'",'').split(',')
#verifica se o conjunto de dados pode ser baixado procurando por um botão "Baixar"
def contemBotaoDownload():
    candidatos = CONST_BROWSER.find_elements(By.CLASS_NAME,"btn")
    for candidato in candidatos:
        
        if candidato.text =="Baixar":
            return True
    return False
#
def isDataValida(data):
    try: 
        dia,_,mes,_,ano = data.split(" ")
        diasDoMes = Calendar().monthdayscalendar(int(ano),CONST_MESES_DO_ANO[mes])
        diasDoMes = achataLista(diasDoMes)
        if int(dia) in diasDoMes:
            return True
        else:
            return False
    except ValueError:
        log = open("log_erro_data_invalida",'a',encoding="utf-8")
        log.write(data+'\n')
        return False

def getDataUltimoUpdate():
    elementos = CONST_BROWSER.find_elements(By.CLASS_NAME,"metadata-item") 
    for elemento in elementos:
        if elemento.get_attribute("data-test") == "modified":
            candidatos = elemento.find_elements(By.TAG_NAME,"div")
            for candidato in candidatos:
                if isDataValida(candidato.text) or (search(".*:.*",candidato.text) and isDataValida( candidato.text.split(":")[1].lstrip())):
                    return candidato.text
    return False
                
def  getNomeconjuntoDeDadoss():
    return CONST_BROWSER.find_element(By.CLASS_NAME, "content-hero-header").find_element(By.TAG_NAME,"h1").text

def getPeriodoTempo(titulo):
    if (search('[12][09][0-9][0-9]-[12][09][0-9][0-9]',titulo)):
        return search('[12][09][0-9][0-9]-[12][09][0-9][0-9]',titulo).group()
    elif (search('[12][09][0-9][0-9] a [12][09][0-9][0-9]',titulo)):
        return search('[12][09][0-9][0-9] a [12][09][0-9][0-9]',titulo).group()
    elif (search(CONST_MESES_ANO_REGEX+'/[12][09][0-9][0-9]',titulo)):
        return search(CONST_MESES_ANO_REGEX+'/[12][09][0-9][0-9]',titulo).group()
    elif (search('em [12][09][0-9][0-9]',titulo)):
        return search('em [12][09][0-9][0-9]',titulo).group()
    else:
        return None

def handleFeatureLayer():
    botao = CONST_BROWSER.find_element(By.TAG_NAME,"button")
    botao.click()
    sleep(1)
    return CONST_BROWSER.execute_script("let nome_itens = [];let arcgis_hub_download_list_itens = document.getElementsByTagName('arcgis-hub-download-list')[0].shadowRoot.querySelectorAll('*');for (let index = 0; index < arcgis_hub_download_list_itens.length; index++) {nome_itens.push(arcgis_hub_download_list_itens[index].shadowRoot.querySelector('download-option-card').querySelector('download-option-card-header').querySelector('download-option-card-title').innerHTML);}; return nome_itens;")

def getFormato():
    elementos = CONST_BROWSER.find_elements(By.CLASS_NAME,"metadata-item")
    for elemento in elementos:
        if elemento.get_attribute("data-test") == "type":
            arquivo = elemento.find_element(By.CSS_SELECTOR,".content-metadata .metadata-item div:nth-of-type(2)")
            if arquivo.text == "Feature Layer":
                return ['csv','shapefile','geojson','kml']
            else:
                return [arquivo.text]
def getAcesso():
    try:
        elementos = CONST_BROWSER.find_elements(By.CLASS_NAME,"metadata-item")
        for elemento in elementos:
            if elemento.get_attribute("data-test") == "access":
                return elemento.find_element(By.CSS_SELECTOR,".content-metadata .metadata-item div:first-of-type").text
    except:
        return None
def getDescricao():
    descricao = {}
    sleep(5)
    try:
        itensCalciteLabels = CONST_BROWSER.execute_script("let calcite_accordion;let calcite_labels=[]; let arcgis_hub_attributes_list_children = document.getElementsByTagName('arcgis-hub-attributes-list')[0].shadowRoot.querySelectorAll('*'); for (let index = 0; index < arcgis_hub_attributes_list_children.length; index++) { if (arcgis_hub_attributes_list_children[index].tagName == 'CALCITE-ACCORDION') { calcite_accordion = arcgis_hub_attributes_list_children[index]; }; };let calcite_accordion_itens = calcite_accordion.getElementsByTagName('calcite-accordion-item');for (let index = 0; index < calcite_accordion_itens.length; index++) {calcite_labels.push(calcite_accordion_itens[index].getElementsByTagName('calcite-label'));};return calcite_labels;")
        for item in itensCalciteLabels :
            nome = ''
            tipo = ''
            for calciteLabel in item:    
                label, valor =  calciteLabel.text.split('\n')
                if label == "Nome":
                    nome = valor
                elif label == "Tipo":
                    tipo = valor
            descricao.setdefault(nome,tipo)
        return descricao
    except:
        return None
#retorna a  licensa do conjunto de dados
def getLicensa():
    candidatos  =  CONST_BROWSER.find_elements(By.CLASS_NAME,"metadata-item")
    for candidato in candidatos:
        if candidato.get_attribute("data-test")=="license":
            return candidato.find_element(By.TAG_NAME,"div").text.replace("Licença ","")

def getconjuntoDeDados(url,id):
    conjunto ={
            'id':None,
            'nome': None,
            'formato': None,
            'licensa': None,
            'dataPublicacao': None,
            'dataAtualizacao': None,
            'periodoTempo': None,
            'possuiDownload': None,
            'descricao': None,
            'acesso': None
    }
    CONST_BROWSER.get(url)# retorna a página 
    sleep(25) #garante que todo o html da página seja carregada
    try:
        conjunto["id"] = id
        conjunto["nome"] = getNomeconjuntoDeDadoss()
        conjunto['periodoTempo'] = getPeriodoTempo(conjunto["nome"])
        conjunto["possuiDownload"] = contemBotaoDownload()
        conjunto["dataAtualizacao"] = getDataUltimoUpdate()
        conjunto["descricao"] = getDescricao()
        conjunto["formato"] = getFormato()
        conjunto["licensa"] = getLicensa()
        conjunto['acesso'] = getAcesso()
        return conjunto
    except:
        print(id)
        print(url)
        return conjunto
# retorna o elemento footer da página principal
def getFooterPaginaPrincipal():
    sleep(35)
    script = "return document.getElementsByTagName('arcgis-hub-gallery')[0].shadowRoot.querySelector('.gallery-main').querySelector('.gallery-list').querySelector('.gallery-list-footer');"
    return CONST_BROWSER.execute_script(script)

# retorna o botão mais resultados da página principal
def getBotaoMaisResultados():
    footer = getFooterPaginaPrincipal()
    candidato = footer.find_element(By.TAG_NAME,"calcite-button")
    if candidato.get_attribute("class") =="back-to-top-btn":
        return None
    else:
        return candidato

def getCards():
    sleep(1)
    return CONST_BROWSER.execute_script("let cards = [];let arc_hub_entity_cards = document.getElementsByTagName('arcgis-hub-gallery')[0].shadowRoot.querySelector('.gallery-main').querySelector('.gallery-list').getElementsByTagName('arcgis-hub-gallery-layout-list')[0].shadowRoot.querySelector('.card-container').getElementsByTagName('arcgis-hub-entity-card');for (let index = 0; index < arc_hub_entity_cards.length; index++) { cards.push(arc_hub_entity_cards[index].shadowRoot.querySelector('*').shadowRoot.querySelector('*')); };return cards;")

def parseLink(url):
    return (url + "/about").replace("/maps/","/datasets/")

def extraiLinks():
    cards = getCards()
    links = []
    for card in cards:
        link = card.find_element(By.TAG_NAME,'a').get_attribute('href')
        links.append(parseLink(link))
    
    return links

def exportarSaida(conjuntosDeDados):
    
    try:
        campos = list(conjuntosDeDados[0].keys())
        linhas = []

        for conjunto in conjuntosDeDados:
            linhas.append(list(conjunto.values()))
    except:
        print(conjunto)
    with open("metricasNivelAberturaDataRio" + str(date.today().strftime("%Y%m%d%H%M%S"))+".csv", 'w', encoding='utf-8',newline='' ) as arquivoSaida:
        csvWriter = writer(arquivoSaida)
        csvWriter.writerow(campos)
        csvWriter.writerows(linhas)
        
def webCrawler():
    conjuntosDeDados  = []
    CONST_BROWSER.get(CONST_URL_INICIAL)# retorna a página 
    sleep(10) #garante que todo o html da página seja carregada
    while True:
      botaoMaisResultados = getBotaoMaisResultados()
      if botaoMaisResultados==None or botaoMaisResultados.text != "Mais resultados":
        break
      else:
        botaoMaisResultados.click()
        sleep(1)# impede erros por clicar antes que o elemento esteja clicável 
    links = set(extraiLinks())
    i = 1
    for link in links:
        conjuntosDeDados.append(getconjuntoDeDados(link,i))
        i+=1
    exportarSaida(conjuntosDeDados)

#Retorna a string parametrizada
def upperString(string):
    return string.upper()
#Um padrão de código que se repetiu durante a implmentação e foi modularizado. Cria um set a partir de uma lista de strings capitalizando todas as letras
def criarStringSetDeLista(lista):
    return set(map(str.lstrip,map(upperString,lista)))
def comparaSetComFormatosDoConjuntoDeDados(conjuntoDeDados,listaComparada):
    CONST_CONJUNTO_COMPARADO = criarStringSetDeLista(listaComparada)
    CONST_CONJUNTO_FORMATO_CONJUNTO_DE_DADOS = criarStringSetDeLista(conjuntoDeDados['formato'].replace('[','').replace(']','').replace("'",'').split(',')) 
    return len(CONST_CONJUNTO_FORMATO_CONJUNTO_DE_DADOS & CONST_CONJUNTO_COMPARADO)>0
#Retorna se os formatos de arquivo em que um conjunto de dados está disponibilizados é ou não legível. Diferentemente da função avaliaProcessavelPorMaquina não se mede o quão legível. Apenas se é.
def isLegivelPorMaquina(conjuntoDeDados):
    return comparaSetComFormatosDoConjuntoDeDados(conjuntoDeDados,['PDF','XLS','CSV','XML','RDF','MiCrosoft Excel','geojson','kml','shapefile','csv collection'])
 
#Calcula o valor do indicador completo de um conjunto de dados
def avaliaCompleto(conjuntoDeDados):           
    return 0.25*(conjuntoDeDados['possuiDownload']=='True') + 0.25*bool(conjuntoDeDados['descricao']) +0.25*isLegivelPorMaquina(conjuntoDeDados)+ 0.25
def avaliaPrimario(conjuntoDeDados):
    return int(comparaSetComFormatosDoConjuntoDeDados(conjuntoDeDados,['csv','geojson','xls','shapefile','kml','csv collection','Microsoft Excel']))
def avaliaOportuno(conjuntoDeDados):
    return (0.3*(conjuntoDeDados['periodoTempo']!='')) +0.3*(conjuntoDeDados['dataAtualizacao']!='')
def avaliaAcessivel(conjuntoDeDados):
    return 1*(conjuntoDeDados['acesso']=='Público' and conjuntoDeDados['licensa'] == 'CC BY 4.0')
def avaliaProcessavelPorMaquina(conjuntoDeDados):
    if comparaSetComFormatosDoConjuntoDeDados(conjuntoDeDados,['kml','nt','rdf','ttl','rdf','xml']):
        return 1
    elif comparaSetComFormatosDoConjuntoDeDados(conjuntoDeDados,['csv','csv collection','geojson','shapefile']):
        return 0.5
    elif comparaSetComFormatosDoConjuntoDeDados(conjuntoDeDados,['pdf','xls','MiCrosoft Excel']):
        return 0.2
    else:
        return 0
def avaliaNaoProprietario(conjuntoDeDados):
    return 1 - (comparaSetComFormatosDoConjuntoDeDados(conjuntoDeDados,['xls','MiCrosoft Excel','shapefile']) and (not comparaSetComFormatosDoConjuntoDeDados(conjuntoDeDados,['kml','csv','geojson','pdf','xml','nt','rdf','ttl'])))
def avaliaLicensaLivre(conjuntoDeDados):
    return int(1 * conjuntoDeDados['licensa'] == 'CC BY 4.0')
        
def avaliaNivelAbertura():
    with open(glob("metricasNivelAberturaDataRio*.csv")[-1],'r',encoding = 'utf-8') as entrada:
        with open("NivelAberturaDataRio" + str(date.today().strftime("%Y%m%d%H%M%S"))+".csv",'w',encoding = 'utf-8', newline = '') as saida:
            csvReader = DictReader(entrada,delimiter=',')
            csvWriter = writer(saida)
            csvWriter.writerow(['ID','nome','completo','primário','oportuno','acessível','processável por máquina','não discriminatório','não proprietário','licensa livre','NAD'])
            for row in csvReader:
                nivelDeAbertura = {
                    'id'                  : row['id'],
                    'nome'                : row['nome'],
                    'completo'            : avaliaCompleto(row),
                    'primario'            : avaliaPrimario(row),
                    'opotuno'             : avaliaOportuno(row),
                    'acessivel'           : avaliaAcessivel(row),
                    'procesavelPorMaquina': avaliaProcessavelPorMaquina(row),
                    'naoDiscriminatorio'  : 1,
                    'naoProprietario'     : avaliaNaoProprietario(row),
                    'licensaLivre'        : avaliaLicensaLivre(row),
                    'NAD': None
                }
                nivelDeAbertura['NAD'] ="{:.2f}".format(nivelDeAbertura['completo'] + nivelDeAbertura['primario']+ nivelDeAbertura['opotuno'] + nivelDeAbertura['acessivel'] +nivelDeAbertura['procesavelPorMaquina'] + nivelDeAbertura['naoDiscriminatorio'] + nivelDeAbertura['licensaLivre'])
                csvWriter.writerow(list(nivelDeAbertura.values()))

if __name__ =='__main__':
    print("1 - Apenas Web crawling\n2 - Apenas cálculo do nível de abertura\n3-Web crawling e cálculo do nível de abertura")
    funcionalidade = input("Escolha a funcionalidade: ")
    if(funcionalidade == '1'):
        webCrawler()
    elif(funcionalidade=='2'):
        avaliaNivelAbertura()
    elif(funcionalidade=='3'):
        webCrawler()
        avaliaNivelAbertura()
    else:
        print("Funcionalidade desconhecida")
        
    
    
#getconjuntoDeDados('https://www.data.rio/documents/7ce897207dfa4da0bd9e951259121980/about',1)
