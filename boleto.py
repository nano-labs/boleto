# -*- encoding: utf-8 -*-
#!/opt/local/bin python2.7

import Image
from numpy import array, linalg
import pylab


class Barcode():
    '''Leitor de código de barras de boletos bancarios seguindo as instruções do FEBRABAM
       http://www.febraban.org.br/7Rof7SWg6qmyvwJcFwF7I0aSDf9jyV/sitefebraban/Codbar4-v28052004.pdf
    '''

    def __init__(self, imagem=None, arquivo=None):
        if arquivo:
            self.imagem = Image.open(arquivo)
        else:
            self.imagem = imagem
        # O dicionário i25 traduz as sequencias de barras finas (narow) e grossas (Wide)
        # em números.
        # http://en.wikipedia.org/wiki/Interleaved_2_of_5
        self.i25 = {'nnWWn': '0',
                    'WnnnW': '1',
                    'nWnnW': '2',
                    'WWnnn': '3',
                    'nnWnW': '4',
                    'WnWnn': '5',
                    'nWWnn': '6',
                    'nnnWW': '7',
                    'WnnWn': '8',
                    'nWnWn': '9'}

    def line_curve(self, linha):
        '''Recebe uma lista de valores e retorna no formato:
            [[x, y], [x, y], [x, y]]
           Onde y são os valores da lista e x o indice
        '''
        return [[i, linha[i]] for i in range(len(linha))]

    def get_line(self, scanheight=1, offset=0):
        '''Retorna uma lista com a luminancia de cada pixel de uma linha
        retirada de meia altura da imagem. O offset leva essa linha mais
        para cima (-offset) ou para baixo (+offset) da imagem
        '''
        l, a = self.imagem.size
        scanbox = (0, (a / 2) + offset, l, (a / 2) + scanheight + offset)

        r = self.imagem.crop(scanbox)
        bar = Image.new(self.imagem.mode, (l, scanheight))
        bar.paste(r)
        bar = bar.convert('L')

        # bar.show()
        if scanheight > 1:
            bar = bar.resize((l, 1))
        linha = [i for i in bar.getdata()]
        return linha

    def reg_lin(self, linha, plot=False):
        '''Retorna a tangente e afastamento da curva da regressao linear a
        partir de uma lista de valores de Y'''
        T = array([range(len(linha)), [1] * len(linha)]).T
        a, b = linalg.lstsq(T, linha)[0]

        if plot:
            curva = [(a * i) + b for i in range(len(linha))]
            pylab.plot(range(len(linha)), curva, 'r-', range(len(linha)), linha, 'o')
            pylab.show()

        return (a, b)

    def binarizar(self, linha, tg, yzero):
        '''Dada uma lista de valores de Y e a curva da regressao linear é
        retornado 1 para valores acima da curva e 0 para valores abaixo'''
        r = []
        for x, y in self.line_curve(linha):
            if y >= tg * x + yzero:
                r.append(1)
            else:
                r.append(0)
        return r

    def agrupar(self, bin):
        '''Agrupa valores iguais de uma sequencia.
        Ex:
        In: [0,0,0,0,1,1,1,1,1,0,0,0,1,0,1,1,1,0,0,0,0]
        Out: [4,5,3,1,1,3,4]'''
        r = []
        largura = 0
        atual = bin[0]
        for i in bin:
            if i == atual:
                largura += 1
            else:
                r.append(largura)
                largura = 1
            atual = i
        if largura > 1:
            r.append(largura)
        return r

    def barcode_image(self, bin=None, altura=50):
        '''Gera um pseudo-codigo de barras baseado numa lista binária'''
        if not bin:
            bin = self.bin
        b = Image.new('1', (len(bin), 1))
        b.putdata(bin)
        b = b.resize((len(bin), altura))
        return b

    def show_scan(self, linhas=50, bloco=10):
        '''Gera uma imagem resultante da varredura de X linhas do centro
        da imagem, tendo cada linha expandida a um bloco de Y pixels'''
        scan = Image.new('1', (self.imagem.size[0], linhas * bloco))
        for i in range(linhas):
            linha = self.get_line(1, i)
            tg, yzero = self.reg_lin(linha, plot=False)
            bin = self.binarizar(linha, tg, yzero)
            barcode = self.barcode_image(bin, bloco)
            b = barcode.copy()
            scan.paste(b, (0, i * b.size[1], b.size[0], (i + 1) * b.size[1]))
        scan.show()

    def DAC(self, sequencia, modulo=10):
        '''Digito de auto-conferencia. Algoritimo definido pela FEBRABAN'''
        if modulo == 10:
            multiplicador = '21' * len(sequencia)
            multiplicador = multiplicador[:len(sequencia)]
            multiplicador = list(multiplicador)
            multiplicador.reverse()
            multiplicador = ''.join(multiplicador)
            resultados = ''
            for i in range(len(sequencia)):
                resultados += str((int(sequencia[i]) * int(multiplicador[i])))
            soma = 0
            for i in resultados:
                soma += int(i)
            digito = 10 - (soma - ((soma / int(modulo)) * modulo))

        elif modulo == 11:
            multiplicador = '43298765432'
            multiplicador = '23456789' * len(sequencia)
            multiplicador = multiplicador[:len(sequencia)]
            multiplicador = list(multiplicador)
            multiplicador.reverse()
            multiplicador = ''.join(multiplicador)
            soma = 0
            for i in range(len(sequencia)):
                soma += (int(sequencia[i]) * int(multiplicador[i]))
            digito = soma - ((soma / int(modulo)) * modulo)

        return digito

    def check_DAC_geral(self, sequencia):
        if sequencia[2] in ['6', '7']:
            modulo = 10
        elif sequencia[2] in ['8', '9']:
            modulo = 11
        s = '%s%s' % (sequencia[:3], sequencia[4:])
        digito = self.DAC(s, modulo)
        if sequencia[3] == str(digito):
            return True
        else:
            return False

    def barcode_data(self):
        '''Retorna o código de barras encontrado numa imagem ou None'''
        linha = self.get_line()
        tg, yzero = self.reg_lin(linha, plot=False)
        bin = self.binarizar(linha, tg, yzero)
        self.bin = bin
        barras = self.agrupar(bin)[1:-1]
        tg, yzero = self.reg_lin(barras)
        leitura = []
        for i in self.binarizar(barras, tg, yzero):
            leitura.append('W' if i == 1 else 'n')
        codigo = []
        for i in range(4, len(leitura) - 4, 10):
            b = ''.join(leitura[i:i + 10])
            bloco_a = '%s%s%s%s%s' % (b[0], b[2], b[4], b[6], b[8])
            bloco_b = '%s%s%s%s%s' % (b[1], b[3], b[5], b[7], b[9])
            valor = '%s%s' % (self.i25.get(bloco_a, 'X'), self.i25.get(bloco_b, 'X'))
            # print bloco_a, bloco_b, valor
            codigo.append(valor)
        # print ''.join(leitura), len(leitura)
        codigo = ''.join(codigo)
        if 'X' in codigo:
            return None
        else:
            b1 = codigo[:11]
            d1 = self.DAC(b1, 10)
            b2 = codigo[11:22]
            d2 = self.DAC(b2, 10)
            b3 = codigo[22:33]
            d3 = self.DAC(b3, 10)
            b4 = codigo[33:44]
            d4 = self.DAC(b4, 10)
            check = '%s%s%s%s' % (b1, b2, b3, b4)
            print self.check_DAC_geral(check)
            return '%s-%s %s-%s %s-%s %s-%s' % (b1, d1, b2, d2, b3, d3, b4, d4)

if __name__ == "__main__":
    a = Barcode(arquivo='barcode.jpg')
    # show_scan(im, 1, 50)
    print a.barcode_data()
