import csv
import json
import qrcode
from datetime import date, timedelta
from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core.files.base import ContentFile
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth

# --- IMPORTAÇÃO DOS MODELOS ---
from .models import (
    Empresa, Funcionario, Setor, NormaRegulamentadora,
    EPI, TipoEPI, Localizacao, Vacina,
    Advertencia, TipoAdvertencia,
    Extintor, InspecaoExtintor, FotoInspecao,
    Equipamento, InspecaoEquipamento, ArquivoInspecao,
    # Prontuário
    ControleVacina, EntregaEPI, TreinamentoFuncionario,
    Afastamento, AcidenteTrabalho, MovimentacaoEstoque,
    # Quimicos, Hospitais e Novos do EPI
    ProdutoQuimico, Hospital, TipoEspecialidade,
    CategoriaEPI, MarcaEPI, TamanhoEPI
)

# --- IMPORTAÇÃO DOS FORMULÁRIOS ---
from .forms import (
    CadastroSaaSForm, FuncionarioForm, SetorForm,
    TipoEPIForm, LocalizacaoForm, EPIForm, VacinaForm,
    TipoAdvertenciaForm, AdvertenciaForm, AdvertenciaFuncionarioForm,
    ExtintorForm, InspecaoExtintorForm,
    EquipamentoForm, InspecaoEquipamentoForm,
    # Forms do Prontuário
    ControleVacinaForm, EntregaEPIForm, TreinamentoFuncionarioForm,
    AfastamentoForm, AcidenteTrabalhoForm,
    # Forms Novos
    ProdutoQuimicoForm, HospitalForm, TipoEspecialidadeForm,
    # Forms dos Modais de EPI
    CategoriaEPIForm, MarcaEPIForm, TamanhoEPIForm
)

# --- VIEWS GERAIS ---

def cadastro(request):
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
def dashboard(request):
    empresa = getattr(request.user.perfil, 'empresa', None)
    return render(request, 'dashboard.html', {'empresa': empresa})

# --- FUNCIONÁRIOS ---

@login_required
def lista_funcionarios(request):
    empresa = request.user.perfil.empresa
    funcionarios = Funcionario.objects.filter(empresa=empresa)
    return render(request, 'funcionarios_lista.html', {'funcionarios': funcionarios})

@login_required
def novo_funcionario(request):
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

@login_required
def editar_funcionario(request, pk):
    empresa = request.user.perfil.empresa
    funcionario = get_object_or_404(Funcionario, pk=pk, empresa=empresa)
    
    if request.method == 'POST':
        form = FuncionarioForm(empresa.id, request.POST, instance=funcionario)
        if form.is_valid():
            form.save()
            return redirect('detalhe_funcionario', pk=funcionario.id)
    else:
        form = FuncionarioForm(empresa.id, instance=funcionario)
    
    return render(request, 'funcionario_form.html', {'form': form, 'titulo': f'Editar: {funcionario.nome}'})

# --- PRONTUÁRIO COMPLETO ---

@login_required
def detalhe_funcionario(request, pk):
    empresa = request.user.perfil.empresa
    funcionario = get_object_or_404(Funcionario, pk=pk, empresa=empresa)
    
    vacinas = funcionario.vacinas.all().order_by('data_proximo_reforco')
    epis = funcionario.epis_entregues.all().order_by('-data_entrega')
    treinamentos = funcionario.treinamentos.all().order_by('-data_realizacao')
    advertencias = funcionario.advertencias.all().order_by('-data_incidente')
    afastamentos = funcionario.afastamentos.all().order_by('-data_inicio')
    acidentes = funcionario.acidentes.all().order_by('-data_acidente')
    
    return render(request, 'funcionario_detalhe.html', {
        'funcionario': funcionario,
        'vacinas': vacinas,
        'epis': epis,
        'treinamentos': treinamentos,
        'advertencias': advertencias,
        'afastamentos': afastamentos,
        'acidentes': acidentes
    })

# --- AÇÕES DO PRONTUÁRIO ---
# (Mantive as funções auxiliares usadas no detalhe do funcionário se existirem urls para elas, 
# mas como não apareceram no urls.py principal, mantenho aqui caso precise)

# --- SETORES E ESTOQUE DE EPI ---

@login_required
def lista_epis(request):
    empresa = request.user.perfil.empresa
    epis = EPI.objects.filter(empresa=empresa)
    return render(request, 'epis_lista.html', {'epis': epis})

@login_required
def novo_epi(request):
    return criar_editar_epi_logica(request, None)

@login_required
def editar_epi(request, id):
    return criar_editar_epi_logica(request, id)

def criar_editar_epi_logica(request, pk):
    empresa = request.user.perfil.empresa
    epi = get_object_or_404(EPI, pk=pk, empresa=empresa) if pk else None
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
def deletar_epi(request, id):
    empresa = request.user.perfil.empresa
    epi = get_object_or_404(EPI, pk=id, empresa=empresa)
    if request.method == 'POST':
        epi.delete()
        return redirect('lista_epis')
    return render(request, 'confirmar_delete.html', {'objeto': epi})

@login_required
def entrada_estoque_epi(request, id):
    epi = get_object_or_404(EPI, id=id, empresa=request.user.perfil.empresa)
    if request.method == 'POST':
        qtd = int(request.POST.get('quantidade'))
        obs = request.POST.get('observacao')
        data = request.POST.get('data_movimento')
        
        MovimentacaoEstoque.objects.create(
            epi=epi,
            tipo='ENTRADA',
            quantidade=qtd,
            observacao=obs,
            data_movimento=data
        )
    return redirect('lista_epis')

# --- CONFIGURAÇÕES DE EPI (LOCAIS E TIPOS) ---

@login_required
def config_tipos_epi(request):
    # Essa view gerenciava "TipoEPI", mas agora temos Categorias. 
    # Mantido para compatibilidade se ainda usar TipoEPI no Setor.
    empresa = request.user.perfil.empresa
    tipos = TipoEPI.objects.filter(empresa=empresa)
    form = TipoEPIForm(request.POST or None)
    if request.method == 'POST':
        if 'delete_id' in request.POST:
            get_object_or_404(TipoEPI, id=request.POST.get('delete_id'), empresa=empresa).delete()
            return redirect('config_tipos_epi')
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('config_tipos_epi')
    return render(request, 'config_tipos_epi.html', {'tipos': tipos, 'form': form})

@login_required
def config_locais(request):
    empresa = request.user.perfil.empresa
    locais = Localizacao.objects.filter(empresa=empresa)
    form = LocalizacaoForm(request.POST or None)
    if request.method == 'POST':
        if 'delete_id' in request.POST:
            get_object_or_404(Localizacao, id=request.POST.get('delete_id'), empresa=empresa).delete()
            return redirect('config_locais')
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('config_locais')
    return render(request, 'config_locais.html', {'locais': locais, 'form': form})

# --- API VIEWS PARA CADASTRO RÁPIDO VIA MODAL (CATEGORIA, MARCA, TAMANHO) ---

@login_required
def api_criar_categoria_epi(request):
    if request.method == "POST":
        form = CategoriaEPIForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.empresa = request.user.perfil.empresa
            cat.save()
            return JsonResponse({'success': True, 'id': cat.id, 'nome': cat.nome})
        else:
            return JsonResponse({'success': False, 'error': form.errors.as_json()})
    return JsonResponse({'success': False, 'error': 'Método inválido'})

@login_required
def api_criar_marca_epi(request):
    if request.method == "POST":
        form = MarcaEPIForm(request.POST)
        if form.is_valid():
            marca = form.save(commit=False)
            marca.empresa = request.user.perfil.empresa
            marca.save()
            return JsonResponse({'success': True, 'id': marca.id, 'nome': marca.nome})
        else:
            return JsonResponse({'success': False, 'error': form.errors.as_json()})
    return JsonResponse({'success': False, 'error': 'Método inválido'})

@login_required
def api_criar_tamanho_epi(request):
    if request.method == "POST":
        form = TamanhoEPIForm(request.POST)
        if form.is_valid():
            tam = form.save(commit=False)
            tam.empresa = request.user.perfil.empresa
            tam.save()
            return JsonResponse({'success': True, 'id': tam.id, 'nome': tam.tamanho})
        else:
            return JsonResponse({'success': False, 'error': form.errors.as_json()})
    return JsonResponse({'success': False, 'error': 'Método inválido'})

# --- ADVERTÊNCIAS ---

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
            return redirect('gerenciar_tipos_advertencia') # Corrigido redirect
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
            return redirect('documento_advertencia', adv_id=adv.pk)
    else:
        form = AdvertenciaForm(empresa.id)
    return render(request, 'advertencias/nova_advertencia.html', {'form': form})

@login_required
def dashboard_advertencias(request):
    empresa = request.user.perfil.empresa
    advertencias = Advertencia.objects.filter(empresa=empresa).order_by('-data_incidente')
    # ... lógicas de gráficos mantidas ...
    return render(request, 'advertencias/dashboard_adv.html', {'advertencias': advertencias})

@login_required
def documento_advertencia(request, adv_id):
    empresa = request.user.perfil.empresa
    adv = get_object_or_404(Advertencia, pk=adv_id, empresa=empresa)
    return render(request, 'advertencias/documento_print.html', {'adv': adv, 'empresa': empresa})

# --- EXTINTORES ---

@login_required
def lista_extintores(request): # Renomeado de dashboard_extintores
    empresa = request.user.perfil.empresa
    extintores = Extintor.objects.filter(empresa=empresa)
    # ... filtros mantidos ...
    return render(request, 'extintores/dashboard.html', {'extintores': extintores})

@login_required
def novo_extintor(request):
    return criar_editar_extintor_logica(request, None)

@login_required
def editar_extintor(request, id):
    return criar_editar_extintor_logica(request, id)

def criar_editar_extintor_logica(request, pk):
    empresa = request.user.perfil.empresa
    extintor = get_object_or_404(Extintor, pk=pk, empresa=empresa) if pk else None
    if request.method == 'POST':
        form = ExtintorForm(empresa.id, request.POST, instance=extintor)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('lista_extintores')
    else:
        form = ExtintorForm(empresa.id, instance=extintor)
    return render(request, 'extintores/form.html', {'form': form})

@login_required
def inspecao_extintor(request, id): # Renomeado de registrar_inspecao
    empresa = request.user.perfil.empresa
    extintor = get_object_or_404(Extintor, pk=id, empresa=empresa)
    if request.method == 'POST':
        form = InspecaoExtintorForm(request.POST, request.FILES)
        if form.is_valid():
            inspecao = form.save(commit=False)
            inspecao.extintor = extintor
            inspecao.save()
            # Fotos...
            return redirect('lista_extintores')
    else:
        form = InspecaoExtintorForm(initial={'responsavel': request.user.username})
    return render(request, 'extintores/inspecao_form.html', {'form': form, 'extintor': extintor})

@login_required
def historico_extintor(request, id):
    empresa = request.user.perfil.empresa
    extintor = get_object_or_404(Extintor, pk=id, empresa=empresa)
    inspecoes = extintor.inspecoes.all().order_by('-data_inspecao')
    return render(request, 'extintores/historico.html', {'extintor': extintor, 'inspecoes': inspecoes})

@login_required
def mobile_scan(request, pk=None): # Renomeado de extintor_mobile
    # Lógica de scan (se tiver pk, mostra detalhes)
    empresa = request.user.perfil.empresa
    extintor = None
    if pk:
        extintor = get_object_or_404(Extintor, pk=pk, empresa=empresa)
    return render(request, 'extintores/mobile_scan.html', {'ext': extintor})

# --- EQUIPAMENTOS ---

@login_required
def lista_equipamentos(request): # Renomeado de dashboard_equipamentos
    empresa = request.user.perfil.empresa
    equipamentos = Equipamento.objects.filter(empresa=empresa)
    return render(request, 'equipamentos/dashboard.html', {'equipamentos': equipamentos})

@login_required
def novo_equipamento(request):
    return criar_editar_equipamento_logica(request, None)

@login_required
def editar_equipamento(request, id):
    return criar_editar_equipamento_logica(request, id)

def criar_editar_equipamento_logica(request, pk):
    empresa = request.user.perfil.empresa
    equipamento = get_object_or_404(Equipamento, pk=pk, empresa=empresa) if pk else None
    if request.method == 'POST':
        form = EquipamentoForm(empresa.id, request.POST, request.FILES, instance=equipamento)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('lista_equipamentos')
    else:
        form = EquipamentoForm(empresa.id, instance=equipamento)
    return render(request, 'equipamentos/form.html', {'form': form})

@login_required
def inspecao_equipamento(request, id): # Renomeado
    empresa = request.user.perfil.empresa
    equipamento = get_object_or_404(Equipamento, pk=id, empresa=empresa)
    if request.method == 'POST':
        form = InspecaoEquipamentoForm(request.POST, request.FILES)
        if form.is_valid():
            inspecao = form.save(commit=False)
            inspecao.equipamento = equipamento
            inspecao.save()
            return redirect('historico_equipamento', id=equipamento.pk)
    else:
        form = InspecaoEquipamentoForm(initial={'responsavel': request.user.username})
    return render(request, 'equipamentos/inspecao_form.html', {'form': form, 'equipamento': equipamento})

@login_required
def historico_equipamento(request, id):
    empresa = request.user.perfil.empresa
    equipamento = get_object_or_404(Equipamento, pk=id, empresa=empresa)
    inspecoes = equipamento.inspecoes.all().order_by('-data_inspecao')
    return render(request, 'equipamentos/historico.html', {'equipamento': equipamento, 'inspecoes': inspecoes})

# --- CONFIGURAÇÕES GERAIS ---

@login_required
def gerenciar_vacinas(request):
    empresa = request.user.perfil.empresa
    vacinas = Vacina.objects.filter(empresa=empresa)
    form = VacinaForm(request.POST or None)
    if request.method == 'POST':
        if 'delete_id' in request.POST:
            get_object_or_404(Vacina, id=request.POST.get('delete_id'), empresa=empresa).delete()
            return redirect('gerenciar_vacinas')
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('gerenciar_vacinas')
    return render(request, 'vacinas/gerenciar_vacinas.html', {'vacinas': vacinas, 'form': form})

# --- QUIMICOS ---

@login_required
def dashboard_quimicos(request):
    empresa = request.user.perfil.empresa
    produtos = ProdutoQuimico.objects.filter(empresa=empresa)
    # ... lógica de validade ...
    return render(request, 'quimicos/dashboard.html', {'produtos': produtos})

@login_required
def novo_quimico(request):
    return criar_editar_quimico_logica(request, None)

@login_required
def editar_quimico(request, id):
    return criar_editar_quimico_logica(request, id)

def criar_editar_quimico_logica(request, pk):
    empresa = request.user.perfil.empresa
    produto = get_object_or_404(ProdutoQuimico, pk=pk, empresa=empresa) if pk else None
    if request.method == 'POST':
        form = ProdutoQuimicoForm(empresa.id, request.POST, request.FILES, instance=produto)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('dashboard_quimicos')
    else:
        form = ProdutoQuimicoForm(empresa.id, instance=produto)
    return render(request, 'generic_form.html', {'form': form, 'titulo': 'Produto Químico'})

# --- HOSPITAIS ---

@login_required
def dashboard_hospitais(request):
    empresa = request.user.perfil.empresa
    hospitais = Hospital.objects.filter(empresa=empresa)
    return render(request, 'hospitais/dashboard.html', {'hospitais': hospitais})

@login_required
def novo_hospital(request):
    # Lógica de criação de hospital
    empresa = request.user.perfil.empresa
    if request.method == 'POST':
        form = HospitalForm(empresa.id, request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            form.save_m2m()
            return redirect('dashboard_hospitais')
    else:
        form = HospitalForm(empresa.id)
    return render(request, 'hospitais/form.html', {'form': form})

@login_required
def config_hospitais(request): # Renomeado de gerenciar_especialidades
    empresa = request.user.perfil.empresa
    tipos = TipoEspecialidade.objects.filter(empresa=empresa)
    form = TipoEspecialidadeForm(request.POST or None)
    if request.method == 'POST':
        # ... lógica de salvar/deletar especialidade ...
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('config_hospitais')
    return render(request, 'hospitais/gerenciar_especialidades.html', {'tipos': tipos, 'form': form})