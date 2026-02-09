import csv
import json
import qrcode
from datetime import date, timedelta
from io import BytesIO
# Em core/views.py
from django.db.models import Count, Q
from .models import ProdutoQuimico, RiscoOcupacional, Setor
from .forms import ProdutoQuimicoForm, RiscoOcupacionalForm
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core.files.base import ContentFile
from django.db.models import Count, Q, ProtectedError
from django.db.models.functions import TruncMonth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import ProdutoQuimicoSerializer

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
    CategoriaEPI, MarcaEPI, TamanhoEPI, ExposicaoOcupacional
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
def editar_funcionario(request, id):
    empresa = request.user.perfil.empresa
    funcionario = get_object_or_404(Funcionario, pk=id, empresa=empresa)
    
    if request.method == 'POST':
        form = FuncionarioForm(empresa.id, request.POST, instance=funcionario)
        if form.is_valid():
            form.save()
            return redirect('detalhe_funcionario', id=funcionario.id)
    else:
        form = FuncionarioForm(empresa.id, instance=funcionario)
    
    return render(request, 'funcionario_form.html', {'form': form, 'titulo': f'Editar: {funcionario.nome}'})

# --- PRONTUÁRIO COMPLETO ---

@login_required
def detalhe_funcionario(request, id):
    empresa = request.user.perfil.empresa
    funcionario = get_object_or_404(Funcionario, pk=id, empresa=empresa)
    
    # Listagens
    vacinas = funcionario.vacinas.all().order_by('data_proximo_reforco')
    epis = funcionario.epis_entregues.all().order_by('-data_entrega')
    treinamentos = funcionario.treinamentos.all().order_by('-data_realizacao')
    advertencias = funcionario.advertencias.all().order_by('-data_incidente')
    afastamentos = funcionario.afastamentos.all().order_by('-data_inicio')
    acidentes = funcionario.acidentes.all().order_by('-data_acidente')
    
    # Formulários para os Modais
    context = {
        'funcionario': funcionario,
        'vacinas': vacinas,
        'epis': epis,
        'treinamentos': treinamentos,
        'advertencias': advertencias,
        'afastamentos': afastamentos,
        'acidentes': acidentes,
        
        # Forms Vazios
        'form_vacina': ControleVacinaForm(empresa.id),
        'form_epi': EntregaEPIForm(empresa.id),
        'form_treinamento': TreinamentoFuncionarioForm(),
        'form_advertencia': AdvertenciaFuncionarioForm(empresa.id),
        'form_afastamento': AfastamentoForm(),
        'form_acidente': AcidenteTrabalhoForm(),
    }
    return render(request, 'funcionario_detalhe.html', context)

# --- AÇÕES DO PRONTUÁRIO (VIEWS DE REGISTRO) ---

@login_required
def registrar_vacina(request, func_id):
    empresa = request.user.perfil.empresa
    funcionario = get_object_or_404(Funcionario, pk=func_id, empresa=empresa)
    if request.method == 'POST':
        form = ControleVacinaForm(empresa.id, request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.funcionario = funcionario
            obj.save()
    return redirect('detalhe_funcionario', id=func_id)

@login_required
def registrar_entrega_epi(request, func_id):
    empresa = request.user.perfil.empresa
    funcionario = get_object_or_404(Funcionario, pk=func_id, empresa=empresa)
    if request.method == 'POST':
        form = EntregaEPIForm(empresa.id, request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.funcionario = funcionario
            obj.save()
    return redirect('detalhe_funcionario', id=func_id)

@login_required
def registrar_treinamento(request, func_id):
    empresa = request.user.perfil.empresa
    funcionario = get_object_or_404(Funcionario, pk=func_id, empresa=empresa)
    if request.method == 'POST':
        form = TreinamentoFuncionarioForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.funcionario = funcionario
            obj.save()
    return redirect('detalhe_funcionario', id=func_id)

@login_required
def registrar_afastamento(request, func_id):
    empresa = request.user.perfil.empresa
    funcionario = get_object_or_404(Funcionario, pk=func_id, empresa=empresa)
    if request.method == 'POST':
        form = AfastamentoForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.funcionario = funcionario
            obj.save()
            funcionario.situacao = 'AFASTADO'
            funcionario.save()
    return redirect('detalhe_funcionario', id=func_id)

@login_required
def registrar_acidente(request, func_id):
    empresa = request.user.perfil.empresa
    funcionario = get_object_or_404(Funcionario, pk=func_id, empresa=empresa)
    if request.method == 'POST':
        form = AcidenteTrabalhoForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.funcionario = funcionario
            obj.save()
    return redirect('detalhe_funcionario', id=func_id)

@login_required
def registrar_advertencia_modal(request, func_id):
    empresa = request.user.perfil.empresa
    funcionario = get_object_or_404(Funcionario, pk=func_id, empresa=empresa)
    if request.method == 'POST':
        form = AdvertenciaFuncionarioForm(empresa.id, request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.funcionario = funcionario
            obj.empresa = empresa
            obj.save()
    return redirect('detalhe_funcionario', id=func_id)

# --- SETORES E ESTOQUE DE EPI ---

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

@login_required
def lista_epis(request):
    empresa = request.user.perfil.empresa
    epis = EPI.objects.filter(empresa=empresa, ativo=True) 
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
        try:
            epi.delete()
        except ProtectedError:
            epi.ativo = False
            epi.save()
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

# --- API VIEWS PARA CADASTRO RÁPIDO VIA MODAL ---

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

@login_required
def api_criar_especialidade(request):
    if request.method == "POST":
        from .forms import TipoEspecialidadeForm 
        form = TipoEspecialidadeForm(request.POST)
        if form.is_valid():
            esp = form.save(commit=False)
            esp.empresa = request.user.perfil.empresa
            esp.save()
            return JsonResponse({'success': True, 'id': esp.id, 'nome': esp.nome})
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
            return redirect('gerenciar_tipos_advertencia')
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
    return render(request, 'advertencias/dashboard_adv.html', {'advertencias': advertencias})

@login_required
def documento_advertencia(request, adv_id):
    empresa = request.user.perfil.empresa
    adv = get_object_or_404(Advertencia, pk=adv_id, empresa=empresa)
    return render(request, 'advertencias/documento_print.html', {'adv': adv, 'empresa': empresa})

# --- EXTINTORES ---

@login_required
def lista_extintores(request):
    empresa = request.user.perfil.empresa
    extintores = Extintor.objects.filter(empresa=empresa)
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
def inspecao_extintor(request, id):
    empresa = request.user.perfil.empresa
    extintor = get_object_or_404(Extintor, pk=id, empresa=empresa)
    if request.method == 'POST':
        form = InspecaoExtintorForm(request.POST, request.FILES)
        if form.is_valid():
            inspecao = form.save(commit=False)
            inspecao.extintor = extintor
            inspecao.save()
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
def mobile_scan(request, pk=None):
    empresa = request.user.perfil.empresa
    extintor = None
    if pk:
        extintor = get_object_or_404(Extintor, pk=pk, empresa=empresa)
    return render(request, 'extintores/mobile_scan.html', {'ext': extintor})

# --- EQUIPAMENTOS ---

@login_required
def lista_equipamentos(request):
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
def inspecao_equipamento(request, id):
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
    
    # Produtos Químicos
    produtos = ProdutoQuimico.objects.filter(empresa=empresa)
    total_quimicos = produtos.count()
    
    # Cálculo de validade (Exemplo simples)
    hoje = date.today()
    alerta_quimicos = 0 # Lógica simplificada para evitar erro se campo não existir
    
    # Mapa de Riscos (Setores com seus riscos)
    setores_mapa = Setor.objects.filter(empresa=empresa).prefetch_related('riscos')
    total_setores = setores_mapa.count()
    
    # Riscos Ocupacionais
    todos_riscos = RiscoOcupacional.objects.filter(empresa=empresa)
    total_riscos = todos_riscos.count()
    
    # Form para modal
    form_risco = RiscoOcupacionalForm(empresa.id)

    context = {
        'produtos': produtos,
        'total_quimicos': total_quimicos,
        'alerta_quimicos': alerta_quimicos,
        'setores_mapa': setores_mapa,
        'todos_riscos': todos_riscos,
        'total_riscos': total_riscos,
        'total_setores': total_setores,
        'form_risco': form_risco,
    }
    return render(request, 'quimicos/dashboard.html', context)

# --- VIEWS DE RISCO OCUPACIONAL (Que estavam faltando) ---

@login_required
def criar_risco(request):
    empresa = request.user.perfil.empresa
    if request.method == 'POST':
        form = RiscoOcupacionalForm(empresa.id, request.POST)
        if form.is_valid():
            risco = form.save(commit=False)
            risco.empresa = empresa
            risco.save()
            return redirect('dashboard_quimicos')
    return redirect('dashboard_quimicos')

@login_required
def deletar_risco(request, id):
    empresa = request.user.perfil.empresa
    risco = get_object_or_404(RiscoOcupacional, pk=id, empresa=empresa)
    risco.delete()
    return redirect('dashboard_quimicos')

@login_required
def associar_risco_setor(request, setor_id):
    empresa = request.user.perfil.empresa
    setor = get_object_or_404(Setor, pk=setor_id, empresa=empresa)
    
    if request.method == 'POST':
        riscos_ids = request.POST.getlist('riscos')
        setor.riscos.clear() # Limpa anteriores
        for r_id in riscos_ids:
            r = get_object_or_404(RiscoOcupacional, pk=r_id, empresa=empresa)
            setor.riscos.add(r)
        setor.save()
        
    return redirect('dashboard_quimicos')

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

@login_required
def deletar_quimico(request, pk):
    empresa = request.user.perfil.empresa
    produto = get_object_or_404(ProdutoQuimico, pk=pk, empresa=empresa)
    if request.method == 'POST':
        produto.delete()
        return redirect('dashboard_quimicos')
    return render(request, 'confirmar_delete.html', {'objeto': produto})

# --- HOSPITAIS ---

@login_required
def dashboard_hospitais(request):
    empresa = request.user.perfil.empresa
    hospitais = Hospital.objects.filter(empresa=empresa)
    return render(request, 'hospitais/dashboard.html', {'hospitais': hospitais})

@login_required
def novo_hospital(request):
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
def config_hospitais(request):
    empresa = request.user.perfil.empresa
    tipos = TipoEspecialidade.objects.filter(empresa=empresa)
    form = TipoEspecialidadeForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('config_hospitais')
    return render(request, 'hospitais/gerenciar_especialidades.html', {'tipos': tipos, 'form': form})


@login_required
def dashboard_quimicos(request):
    empresa = request.user.perfil.empresa
    
    # 1. Dados de Inventário
    produtos = ProdutoQuimico.objects.filter(empresa=empresa)
    
    # Filtros simples (busca)
    termo = request.GET.get('busca')
    if termo:
        produtos = produtos.filter(
            Q(nome__icontains=termo) | Q(cas_number__icontains=termo)
        )

    # 2. Dados de Exposição
    exposicoes = ExposicaoOcupacional.objects.filter(empresa=empresa).select_related('funcionario', 'produto_quimico', 'funcionario__setor')
    
    # 3. Dados do Mapa de Riscos (Cálculo Agregado)
    # Agrupa produtos por setor para contar riscos
    setores_risco = []
    setores = Setor.objects.filter(empresa=empresa)
    
    for setor in setores:
        prods_setor = produtos.filter(setor=setor)
        funcionarios_setor = Funcionario.objects.filter(setor=setor).count()
        qtd_produtos = prods_setor.count()
        
        # Lógica simples de nível de risco baseada na quantidade de produtos perigosos
        nivel = 'baixo'
        if qtd_produtos > 10: nivel = 'alto'
        elif qtd_produtos > 5: nivel = 'medio'
        
        # Coletar todos os GHS desse setor
        riscos_setor = set()
        for p in prods_setor:
            riscos_setor.update(p.lista_ghs)
            
        if qtd_produtos > 0: # Só mostra setores com químicos
            setores_risco.append({
                'nome': setor.nome,
                'nivel': nivel,
                'produtos': qtd_produtos,
                'funcionarios': funcionarios_setor,
                'principais_riscos': list(riscos_setor)[:3] # Pega os 3 primeiros
            })

    form = ProdutoQuimicoForm(empresa.id)

    context = {
        'produtos': produtos,
        'exposicoes': exposicoes,
        'setores_risco': setores_risco,
        'form': form,
    }
    return render(request, 'quimicos/dashboard.html', context)


@api_view(['GET'])
#@permission_classes([IsAuthenticated])
def api_lista_quimicos(request):
    """
    Retorna a lista de produtos químicos da empresa do usuário em JSON.
    """
    try:
        empresa = request.user.perfil.empresa
        # CORREÇÃO: Removido .select_related('localizacao') para evitar o erro 500
        produtos = ProdutoQuimico.objects.filter(empresa=empresa)
        serializer = ProdutoQuimicoSerializer(produtos, many=True)
        return Response(serializer.data)
    except AttributeError:
        return Response({"erro": "Usuário sem empresa vinculada"}, status=400)