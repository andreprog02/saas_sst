import csv
import qrcode
from datetime import date, timedelta
from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth

# --- IMPORTAÇÃO DOS MODELOS ---
from .models import (
    Empresa, 
    Funcionario, 
    Setor, 
    NormaRegulamentadora,
    EPI, 
    TipoEPI, 
    Localizacao,
    Vacina,
    Advertencia, 
    TipoAdvertencia,
    Extintor, 
    InspecaoExtintor,
    FotoInspecao,
    # Novos modelos de equipamentos
    Equipamento, 
    InspecaoEquipamento,
    ArquivoInspecao
)

# --- IMPORTAÇÃO DOS FORMULÁRIOS ---
from .forms import (
    CadastroSaaSForm, 
    FuncionarioForm, 
    SetorForm,
    TipoEPIForm, 
    LocalizacaoForm, 
    EPIForm,
    VacinaForm,
    TipoAdvertenciaForm, 
    AdvertenciaForm,
    ExtintorForm, 
    InspecaoExtintorForm,
    # Novos formulários
    EquipamentoForm,
    InspecaoEquipamentoForm
)

# --- VIEWS DE AUTENTICAÇÃO E DASHBOARD ---

def cadastro_view(request):
    if request.method == 'POST':
        form = CadastroSaaSForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CadastroSaaSForm()
    return render(request, 'registration/cadastro.html', {'form': form})

@login_required
def dashboard_view(request):
    try:
        empresa = request.user.perfil.empresa
    except:
        empresa = None
    return render(request, 'dashboard.html', {'empresa': empresa})

# --- VIEWS DE FUNCIONÁRIOS ---

@login_required
def lista_funcionarios(request):
    empresa = request.user.perfil.empresa
    funcionarios = Funcionario.objects.filter(empresa=empresa)
    return render(request, 'funcionarios_lista.html', {'funcionarios': funcionarios})

@login_required
def criar_funcionario(request):
    empresa = request.user.perfil.empresa
    if request.method == 'POST':
        form = FuncionarioForm(empresa.id, request.POST)
        if form.is_valid():
            func = form.save(commit=False)
            func.empresa = empresa
            func.save()
            return redirect('lista_funcionarios')
    else:
        form = FuncionarioForm(empresa.id)
    return render(request, 'funcionario_form.html', {'form': form})

# --- VIEWS DE SETORES ---

@login_required
def criar_setor(request):
    empresa = request.user.perfil.empresa
    if request.method == 'POST':
        form = SetorForm(empresa, request.POST)
        if form.is_valid():
            setor = form.save(commit=False)
            setor.empresa = empresa
            setor.save()
            form.save_m2m()
            return redirect('dashboard')
    else:
        form = SetorForm(empresa)
    return render(request, 'setor_form.html', {'form': form})

# --- VIEWS DE ESTOQUE (EPIs) ---

@login_required
def lista_epis(request):
    empresa = request.user.perfil.empresa
    epis = EPI.objects.filter(empresa=empresa)
    return render(request, 'epis_lista.html', {'epis': epis})

@login_required
def criar_editar_epi(request, pk=None):
    empresa = request.user.perfil.empresa
    if pk:
        epi = get_object_or_404(EPI, pk=pk, empresa=empresa)
    else:
        epi = None
    
    if request.method == 'POST':
        form = EPIForm(empresa.id, request.POST, instance=epi)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('lista_epis')
    else:
        form = EPIForm(empresa.id, instance=epi)
    return render(request, 'epi_form.html', {'form': form})

@login_required
def deletar_epi(request, pk):
    empresa = request.user.perfil.empresa
    epi = get_object_or_404(EPI, pk=pk, empresa=empresa)
    if request.method == 'POST':
        epi.delete()
        return redirect('lista_epis')
    return render(request, 'confirmar_delete.html', {'objeto': epi})

# --- VIEWS DE CONFIGURAÇÕES (Tipos e Locais) ---

@login_required
def gerenciar_tipos(request):
    empresa = request.user.perfil.empresa
    tipos = TipoEPI.objects.filter(empresa=empresa)
    form = TipoEPIForm(request.POST or None)
    
    if request.method == 'POST':
        if 'delete_id' in request.POST:
            obj = get_object_or_404(TipoEPI, id=request.POST.get('delete_id'), empresa=empresa)
            obj.delete()
            return redirect('gerenciar_tipos')
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('gerenciar_tipos')

    return render(request, 'config_tipos_epi.html', {'tipos': tipos, 'form': form})

@login_required
def gerenciar_locais(request):
    empresa = request.user.perfil.empresa
    locais = Localizacao.objects.filter(empresa=empresa)
    form = LocalizacaoForm(request.POST or None)

    if request.method == 'POST':
        if 'delete_id' in request.POST:
            obj = get_object_or_404(Localizacao, id=request.POST.get('delete_id'), empresa=empresa)
            obj.delete()
            return redirect('gerenciar_locais')
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('gerenciar_locais')

    return render(request, 'config_locais.html', {'locais': locais, 'form': form})

@login_required
def gerenciar_vacinas(request):
    empresa = request.user.perfil.empresa
    vacinas = Vacina.objects.filter(empresa=empresa)
    form = VacinaForm(request.POST or None)

    if request.method == 'POST':
        if 'delete_id' in request.POST:
            obj = get_object_or_404(Vacina, id=request.POST.get('delete_id'), empresa=empresa)
            obj.delete()
            return redirect('gerenciar_vacinas')
        
        if 'importar_padrao' in request.POST:
            sugestoes = [
                ("Antitetânica", "Reforço a cada 10 anos"),
                ("Hepatite B", "3 doses (0, 1 e 6 meses)"),
                ("Febre Amarela", "Dose única (áreas de risco)"),
                ("Tríplice Viral", "Sarampo, Caxumba e Rubéola"),
                ("Influenza (Gripe)", "Anual (Campanha)"),
                ("COVID-19", "Conforme esquema vacinal vigente"),
            ]
            for nome, desc in sugestoes:
                Vacina.objects.get_or_create(empresa=empresa, nome=nome, defaults={'descricao': desc})
            return redirect('gerenciar_vacinas')

        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('gerenciar_vacinas')

    return render(request, 'vacinas/gerenciar_vacinas.html', {'vacinas': vacinas, 'form': form})

# --- VIEWS DE ADVERTÊNCIAS ---

@login_required
def gerenciar_tipos_advertencia(request):
    empresa = request.user.perfil.empresa
    tipos = TipoAdvertencia.objects.filter(empresa=empresa)
    
    if request.method == 'POST':
        form = TipoAdvertenciaForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('config_advertencias')
    else:
        form = TipoAdvertenciaForm()
    
    return render(request, 'advertencias/gerenciar_tipos.html', {'tipos': tipos, 'form': form})

@login_required
def nova_advertencia(request):
    empresa = request.user.perfil.empresa
    
    if request.method == 'POST':
        form = AdvertenciaForm(empresa.id, request.POST)
        if form.is_valid():
            adv = form.save(commit=False)
            adv.empresa = empresa
            adv.save()
            return redirect('imprimir_advertencia', pk=adv.pk)
    else:
        form = AdvertenciaForm(empresa.id)
    
    return render(request, 'advertencias/nova_advertencia.html', {'form': form})

@login_required
def dashboard_advertencias(request):
    empresa = request.user.perfil.empresa
    advertencias = Advertencia.objects.filter(empresa=empresa).order_by('-data_incidente')

    por_setor = advertencias.values('funcionario__setor__nome').annotate(total=Count('id')).order_by('-total')
    por_tipo = advertencias.values('tipo__titulo').annotate(total=Count('id')).order_by('-total')
    por_mes = advertencias.annotate(mes=TruncMonth('data_incidente')).values('mes').annotate(total=Count('id')).order_by('mes')

    return render(request, 'advertencias/dashboard_adv.html', {
        'advertencias': advertencias,
        'por_setor': por_setor,
        'por_tipo': por_tipo,
        'por_mes': por_mes
    })

@login_required
def imprimir_advertencia(request, pk):
    empresa = request.user.perfil.empresa
    adv = get_object_or_404(Advertencia, pk=pk, empresa=empresa)
    return render(request, 'advertencias/documento_print.html', {'adv': adv, 'empresa': empresa})

# --- VIEWS DE EXTINTORES ---

@login_required
def dashboard_extintores(request):
    empresa = request.user.perfil.empresa
    extintores = Extintor.objects.filter(empresa=empresa)

    status_filter = request.GET.get('status')
    if status_filter:
        extintores = extintores.filter(situacao=status_filter)
        
    termo = request.GET.get('search')
    if termo:
        extintores = extintores.filter(
            Q(codigo_patrimonial__icontains=termo) | 
            Q(localizacao__nome__icontains=termo)
        )

    total_ativos = extintores.filter(situacao='ATIVO').count()
    
    data_limite = date.today() + timedelta(days=30)
    vencendo_recarga = extintores.filter(data_proxima_manutencao__lte=data_limite, data_proxima_manutencao__gte=date.today()).count()
    vencendo_hidro = extintores.filter(data_teste_hidrostatico__lte=data_limite, data_teste_hidrostatico__gte=date.today()).count()

    data_limite_inspecao = date.today() - timedelta(days=30)
    pendentes_inspecao = []
    for ext in extintores.filter(situacao='ATIVO'):
        ultima = ext.inspecoes.order_by('-data_inspecao').first()
        if not ultima or ultima.data_inspecao < data_limite_inspecao:
            pendentes_inspecao.append(ext)

    return render(request, 'extintores/dashboard.html', {
        'extintores': extintores,
        'total_ativos': total_ativos,
        'vencendo_recarga': vencendo_recarga,
        'vencendo_hidro': vencendo_hidro,
        'qtd_pendente_inspecao': len(pendentes_inspecao),
        'pendentes_inspecao': pendentes_inspecao
    })

@login_required
def criar_editar_extintor(request, pk=None):
    empresa = request.user.perfil.empresa
    if pk:
        extintor = get_object_or_404(Extintor, pk=pk, empresa=empresa)
    else:
        extintor = None

    if request.method == 'POST':
        form = ExtintorForm(empresa.id, request.POST, instance=extintor)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('dashboard_extintores')
    else:
        form = ExtintorForm(empresa.id, instance=extintor)
    
    return render(request, 'extintores/form.html', {'form': form})

@login_required
def registrar_inspecao(request, extintor_id):
    empresa = request.user.perfil.empresa
    extintor = get_object_or_404(Extintor, pk=extintor_id, empresa=empresa)
    
    if request.method == 'POST':
        form = InspecaoExtintorForm(request.POST, request.FILES)
        if form.is_valid():
            inspecao = form.save(commit=False)
            inspecao.extintor = extintor
            inspecao.save()
            
            fotos = request.FILES.getlist('fotos')
            for foto in fotos:
                FotoInspecao.objects.create(inspecao=inspecao, imagem=foto)

            extintor.sinalizacao_ok = inspecao.sinalizacao_visivel
            extintor.acesso_livre = inspecao.acesso_livre
            extintor.save()
            
            return redirect('dashboard_extintores')
    else:
        form = InspecaoExtintorForm(initial={'responsavel': request.user.username})

    return render(request, 'extintores/inspecao_form.html', {'form': form, 'extintor': extintor})

@login_required
def historico_extintor(request, pk):
    empresa = request.user.perfil.empresa
    extintor = get_object_or_404(Extintor, pk=pk, empresa=empresa)
    inspecoes = extintor.inspecoes.all().order_by('-data_inspecao')
    return render(request, 'extintores/historico.html', {'extintor': extintor, 'inspecoes': inspecoes})

@login_required
def exportar_extintores(request):
    empresa = request.user.perfil.empresa
    extintores = Extintor.objects.filter(empresa=empresa)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="extintores.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Patrimonio', 'Local', 'Tipo', 'Venc. Recarga', 'Situação'])
    
    for ext in extintores:
        writer.writerow([
            ext.codigo_patrimonial, 
            ext.localizacao.nome, 
            ext.get_agente_display(), 
            ext.data_proxima_manutencao, 
            ext.get_situacao_display()
        ])
        
    return response

# --- VIEWS DE QR CODE (EXTINTORES) ---

@login_required
def gerar_qrcode(request, pk):
    empresa = request.user.perfil.empresa
    extintor = get_object_or_404(Extintor, pk=pk, empresa=empresa)
    
    if not extintor.qrcode_imagem:
        url_destino = request.build_absolute_uri(reverse('extintor_mobile', args=[pk]))
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(url_destino)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        filename = f'qrcode_extintor_{extintor.id}.png'
        extintor.qrcode_imagem.save(filename, ContentFile(buffer.getvalue()), save=True)
        
        buffer.seek(0)
        return HttpResponse(buffer, content_type="image/png")
    else:
        return HttpResponse(extintor.qrcode_imagem, content_type="image/png")

@login_required
def imprimir_etiqueta(request, pk):
    empresa = request.user.perfil.empresa
    extintor = get_object_or_404(Extintor, pk=pk, empresa=empresa)
    return render(request, 'extintores/etiqueta_print.html', {'ext': extintor})

@login_required
def extintor_mobile(request, pk):
    empresa = request.user.perfil.empresa
    extintor = get_object_or_404(Extintor, pk=pk, empresa=empresa)
    ultimas_inspecoes = extintor.inspecoes.all().order_by('-data_inspecao')[:3]
    return render(request, 'extintores/mobile_scan.html', {'ext': extintor, 'ultimas_inspecoes': ultimas_inspecoes})

# --- VIEWS DE OUTROS EQUIPAMENTOS (HIDRANTES, ALARMES, ETC) ---

@login_required
def dashboard_equipamentos(request):
    empresa = request.user.perfil.empresa
    equipamentos = Equipamento.objects.filter(empresa=empresa).order_by('tipo', 'localizacao')
    
    tipo_filter = request.GET.get('tipo')
    if tipo_filter:
        equipamentos = equipamentos.filter(tipo=tipo_filter)

    return render(request, 'equipamentos/dashboard.html', {
        'equipamentos': equipamentos
    })

@login_required
def criar_editar_equipamento(request, pk=None):
    empresa = request.user.perfil.empresa
    equipamento = get_object_or_404(Equipamento, pk=pk, empresa=empresa) if pk else None
    
    if request.method == 'POST':
        form = EquipamentoForm(empresa.id, request.POST, request.FILES, instance=equipamento)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('dashboard_equipamentos')
    else:
        form = EquipamentoForm(empresa.id, instance=equipamento)
    
    return render(request, 'equipamentos/form.html', {'form': form})

@login_required
def inspecionar_equipamento(request, pk):
    empresa = request.user.perfil.empresa
    equipamento = get_object_or_404(Equipamento, pk=pk, empresa=empresa)
    
    if request.method == 'POST':
        # form = InspecaoEquipamentoForm(request.POST, request.FILES) já valida os arquivos via forms.py
        form = InspecaoEquipamentoForm(request.POST, request.FILES) 
        
        if form.is_valid():
            inspecao = form.save(commit=False)
            inspecao.equipamento = equipamento
            inspecao.save()
            
            # Recupera a lista de arquivos para salvar no modelo auxiliar
            # A validação e limpeza já foram feitas pelo form
            arquivos = request.FILES.getlist('arquivos') 
            for f in arquivos:
                ArquivoInspecao.objects.create(inspecao=inspecao, arquivo=f)

            return redirect('historico_equipamento', pk=equipamento.pk)
    else:
        form = InspecaoEquipamentoForm(initial={'responsavel': request.user.username})
        
    return render(request, 'equipamentos/inspecao_form.html', {'form': form, 'equipamento': equipamento})

@login_required
def historico_equipamento(request, pk):
    empresa = request.user.perfil.empresa
    equipamento = get_object_or_404(Equipamento, pk=pk, empresa=empresa)
    inspecoes = equipamento.inspecoes.all().order_by('-data_inspecao')
    
    return render(request, 'equipamentos/historico.html', {
        'equipamento': equipamento, 
        'inspecoes': inspecoes
    })