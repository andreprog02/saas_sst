import json
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, ProtectedError
from django.contrib.auth import login
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import ProdutoQuimicoSerializer

# --- IMPORTAÇÃO DOS MODELOS (ÚNICA) ---
from .models import (
    Empresa, Funcionario, Setor, Cargo, NormaRegulamentadora, RiscoOcupacional,
    Vacina, TipoExame, MatrizRiscoEPI,
    EPI, TipoEPI, CategoriaEPI, MarcaEPI, TamanhoEPI, EntregaEPI, MovimentacaoEstoque, Localizacao,
    Extintor, InspecaoExtintor, FotoInspecao,
    ProdutoQuimico, ExposicaoOcupacional,
    Equipamento, InspecaoEquipamento, ArquivoInspecao,
    ArCondicionado, EquipamentoNR13,
    Hospital, TipoEspecialidade, Exame,
    Advertencia, TipoAdvertencia, Afastamento, AcidenteTrabalho,
    TreinamentoFuncionario, ControleVacina
)

# --- IMPORTAÇÃO DOS FORMULÁRIOS (ÚNICA) ---
from .forms import (
    CadastroSaaSForm, FuncionarioForm,
    SetorForm, CargoForm, MatrizRiscoEPIForm, TipoExameForm,
    EPIForm, EntregaEPIForm, CategoriaEPIForm, MarcaEPIForm, TamanhoEPIForm, TipoEPIForm, LocalizacaoForm,
    ExtintorForm, InspecaoExtintorForm,
    EquipamentoForm, InspecaoEquipamentoForm,
    ProdutoQuimicoForm, RiscoOcupacionalForm,
    HospitalForm, TipoEspecialidadeForm,
    ArCondicionadoForm, EquipamentoNR13Form,
    VacinaForm, ControleVacinaForm, TreinamentoFuncionarioForm,
    AdvertenciaForm, AdvertenciaFuncionarioForm, TipoAdvertenciaForm,
    AfastamentoForm, AcidenteTrabalhoForm, ExameForm
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

    # --- 1. Filtros (GET) ---
    busca = request.GET.get('busca')
    filtro_status = request.GET.get('status')
    filtro_setor = request.GET.get('setor')
    filtro_cargo = request.GET.get('cargo')

    if busca:
        funcionarios = funcionarios.filter(
            Q(nome__icontains=busca) | 
            Q(cpf__icontains=busca) |
            Q(cargo__icontains=busca)
        )
    
    if filtro_status:
        funcionarios = funcionarios.filter(situacao=filtro_status)
    
    if filtro_setor:
        funcionarios = funcionarios.filter(setor_id=filtro_setor)

    if filtro_cargo:
        funcionarios = funcionarios.filter(cargo=filtro_cargo)

    # --- 2. Estatísticas ---
    total_colaboradores = funcionarios.count()
    total_ativos = funcionarios.filter(situacao='ATIVO').count()
    total_afastados = funcionarios.filter(Q(situacao='AFASTADO') | Q(situacao='FERIAS')).count()

    # --- 3. Dados para os Dropdowns dos Filtros ---
    setores = Setor.objects.filter(empresa=empresa).order_by('nome')
    cargos = Cargo.objects.filter(empresa=empresa).order_by('nome') 

    context = {
        'funcionarios': funcionarios,
        'total_colaboradores': total_colaboradores,
        'total_ativos': total_ativos,
        'total_afastados': total_afastados,
        'setores': setores,
        'cargos': cargos,
        'busca_atual': busca,
        'status_atual': filtro_status,
        'setor_atual': filtro_setor and int(filtro_setor) if filtro_setor else '',
        'cargo_atual': filtro_cargo,
    }
    
    return render(request, 'funcionarios_lista.html', context)


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
    
    # 1. Buscar Matriz
    matriz = MatrizRiscoEPI.objects.filter(
        empresa=empresa, 
        setor=funcionario.setor, 
        cargo=funcionario.cargo
    ).first()

    # --- LÓGICA DE CRUZAMENTO (Matriz vs Histórico) ---

    # [NOVO] E. EPIs (Herança da Matriz + Histórico)
    epis_obrigatorios = []
    if matriz:
        # Pega os Tipos de EPI que a matriz exige
        epis_obrigatorios = matriz.epis_obrigatorios.all()

    # Busca o histórico de entregas reais para este funcionário
    # (Supondo que você tenha o related_name='epis_entregues' no model EntregaEPI ou similar)
    historico_entregas_epi = funcionario.epis_entregues.select_related('epi', 'epi__marca').order_by('-data_entrega')

    # A. EXAMES
    status_exames = []
    if matriz:
        for exame_obrigatorio in matriz.exames.all():
            ultimo = funcionario.exames.filter(tipo__iexact=exame_obrigatorio.nome).order_by('-data_realizacao').first()
            status = 'PENDENTE'
            vencimento = None
            if ultimo:
                status = 'OK'
                if ultimo.data_vencimento:
                    vencimento = ultimo.data_vencimento
                    if vencimento < date.today():
                        status = 'VENCIDO'
            
            status_exames.append({
                'nome': exame_obrigatorio.nome,
                'realizado': ultimo.data_realizacao if ultimo else None,
                'vencimento': vencimento,
                'status': status,
                'arquivo': ultimo.arquivo if ultimo else None
            })

    # B. VACINAS
    status_vacinas = []
    if matriz:
        for vacina_obrigatoria in matriz.vacinas.all():
            ultimo = funcionario.vacinas.filter(vacina=vacina_obrigatoria).order_by('-data_aplicacao').first()
            status = 'PENDENTE'
            proxima = None
            if ultimo:
                status = 'OK'
                proxima = ultimo.data_proximo_reforco
                if proxima and proxima < date.today():
                    status = 'VENCIDO'
            
            status_vacinas.append({
                'nome': vacina_obrigatoria.nome,
                'realizado': ultimo.data_aplicacao if ultimo else None,
                'proxima': proxima,
                'status': status,
                'comprovante': ultimo.comprovante if ultimo else None
            })

    # C. NRs
    status_nrs = []
    if matriz:
        for nr in matriz.nrs.all():
            nome_display = f"{nr.codigo} - {nr.titulo}"
            # Busca flexível pelo código da NR
            ultimo = funcionario.treinamentos.filter(nome_treinamento__icontains=nr.codigo).order_by('-data_realizacao').first()
            
            status = 'PENDENTE'
            validade = None
            if ultimo:
                status = 'OK'
                validade = ultimo.data_validade
                if validade and validade < date.today():
                    status = 'VENCIDO'

            status_nrs.append({
                'nome': nome_display,
                'realizado': ultimo.data_realizacao if ultimo else None,
                'validade': validade,
                'status': status,
                'certificado': ultimo.certificado if ultimo else None
            })

    # D. RISCOS
    riscos_agrupados = {'FISICO': [], 'QUIMICO': [], 'BIOLOGICO': [], 'ERGONOMICO': [], 'ACIDENTE': []}
    if matriz:
        for risco in matriz.riscos.all():
            riscos_agrupados[risco.tipo].append(risco)

    # --- DADOS PARA OS COMBOBOXES DOS MODAIS ---
    # Carregamos todas as opções possíveis para facilitar o cadastro
    todas_vacinas = Vacina.objects.filter(empresa=empresa)
    todos_exames_lista = TipoExame.objects.filter(empresa=empresa)
    todas_nrs_lista = NormaRegulamentadora.objects.all()

    context = {
        'funcionario': funcionario,
        'matriz': matriz,
        
        # [NOVO] Contexto de EPIs
        'epis_obrigatorios': epis_obrigatorios,
        'historico_entregas': historico_entregas_epi, # Usei nome diferente para não conflitar com 'epis' abaixo se quiser
        'hoje': date.today(), # Útil para o template

        # Listas Processadas (Status)
        'status_exames': status_exames,
        'status_vacinas': status_vacinas,
        'status_nrs': status_nrs,
        'riscos_agrupados': riscos_agrupados,
        
        # Listas para Combobox (Sugestões)
        'todas_vacinas': todas_vacinas,
        'todos_exames_lista': todos_exames_lista,
        'todas_nrs_lista': todas_nrs_lista,

        # Históricos Gerais
        'epis': funcionario.epis_entregues.all().order_by('-data_entrega'),
        'advertencias': funcionario.advertencias.all().order_by('-data_incidente'),
        'afastamentos': funcionario.afastamentos.all().order_by('-data_inicio'),
        'acidentes': funcionario.acidentes.all().order_by('-data_acidente'),
        
        # Forms
        'form_vacina': ControleVacinaForm(empresa.id),
        'form_epi': EntregaEPIForm(empresa.id),
        'form_treinamento': TreinamentoFuncionarioForm(),
        'form_advertencia': AdvertenciaFuncionarioForm(empresa.id),
        'form_afastamento': AfastamentoForm(),
        'form_acidente': AcidenteTrabalhoForm(),
        'form_exame': ExameForm(), 
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

def criar_editar_epi_logica(request, epi_id=None):
    empresa = request.user.perfil.empresa
    epi = None
    
    if epi_id:
        epi = get_object_or_404(EPI, pk=epi_id, empresa=empresa)

    if request.method == 'POST':
        # CORREÇÃO AQUI: empresa_id deve ser passado como KWARG
        form = EPIForm(request.POST, instance=epi, empresa_id=empresa.id)
        if form.is_valid():
            novo_epi = form.save(commit=False)
            novo_epi.empresa = empresa
            # Se categoria não vier no save (pois é campo filtro), o tipo já resolve
            novo_epi.save()
            return redirect('lista_epis')
    else:
        # CORREÇÃO AQUI TAMBÉM:
        form = EPIForm(instance=epi, empresa_id=empresa.id)

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
    return JsonResponse({'success': False})

@login_required
def api_criar_marca_epi(request):
    if request.method == "POST":
        form = MarcaEPIForm(request.POST)
        if form.is_valid():
            marca = form.save(commit=False)
            marca.empresa = request.user.perfil.empresa
            marca.save()
            return JsonResponse({'success': True, 'id': marca.id, 'nome': marca.nome})
    return JsonResponse({'success': False})

@login_required
def api_criar_tamanho_epi(request):
    if request.method == "POST":
        form = TamanhoEPIForm(request.POST)
        if form.is_valid():
            tam = form.save(commit=False)
            tam.empresa = request.user.perfil.empresa
            tam.save()
            return JsonResponse({'success': True, 'id': tam.id, 'nome': tam.tamanho})
    return JsonResponse({'success': False})

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
    return JsonResponse({'success': False})

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
    extintores = Extintor.objects.filter(empresa=request.user.perfil.empresa)
    # Filtros
    filtro_status = request.GET.get('status')
    filtro_agente = request.GET.get('agente')
    termo_busca = request.GET.get('busca')

    if filtro_status and filtro_status != 'TODOS':
        extintores = extintores.filter(situacao=filtro_status)
    if filtro_agente and filtro_agente != 'TODOS':
        extintores = extintores.filter(agente=filtro_agente)
    if termo_busca:
        extintores = extintores.filter(
            Q(codigo_patrimonial__icontains=termo_busca) |
            Q(numero_serie__icontains=termo_busca) |
            Q(localizacao__nome__icontains=termo_busca)
        )

    # Stats para cards
    todos_extintores = Extintor.objects.filter(empresa=request.user.perfil.empresa)
    hoje = date.today()
    daqui_30_dias = hoje + timedelta(days=30)
    
    stats = {
        'total': todos_extintores.count(),
        'a_vencer': todos_extintores.filter(
            data_proxima_manutencao__range=[hoje, daqui_30_dias], situacao='ATIVO'
        ).count(),
        'vencidos': todos_extintores.filter(
            Q(situacao='VENCIDO') | Q(data_proxima_manutencao__lt=hoje)
        ).count(),
        'manutencao': todos_extintores.filter(situacao='MANUTENCAO').count()
    }

    context = {
        'extintores': extintores, 'stats': stats,
        'filtro_status': filtro_status, 'filtro_agente': filtro_agente, 'busca_atual': termo_busca
    }
    return render(request, 'extintores/extintores_lista.html', context)

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
    vacinas = Vacina.objects.filter(empresa=empresa).order_by('nome')
    
    if request.method == 'POST':
        form = VacinaForm(request.POST)
        if form.is_valid():
            vacina = form.save(commit=False)
            vacina.empresa = empresa
            vacina.save()
            messages.success(request, 'Vacina cadastrada com sucesso!')
            return redirect('gerenciar_vacinas')
        else:
            messages.error(request, 'Erro ao salvar. Verifique os campos.')
    else:
        form = VacinaForm()
    
    return render(request, 'vacinas/gerenciar_vacinas.html', {
        'vacinas': vacinas, 
        'form': form
    })

@login_required
def popular_vacinas(request):
    empresa = request.user.perfil.empresa
    lista_padrao = [
        ('Antitetânica (dT)', 120, 'Reforço a cada 10 anos.'),
        ('Hepatite B', 0, 'Esquema de 3 doses. Reforço não é rotina.'),
        ('Tríplice Viral', 0, 'Sarampo, Caxumba e Rubéola.'),
        ('Febre Amarela', 0, 'Dose única (áreas de risco).'),
        ('Influenza (Gripe)', 12, 'Dose anual (campanha).'),
        ('COVID-19', 0, 'Conforme calendário MS.'),
    ]
    
    contador = 0
    for nome, meses, desc in lista_padrao:
        _, created = Vacina.objects.get_or_create(
            empresa=empresa,
            nome=nome,
            defaults={'meses_reforco': meses, 'descricao': desc}
        )
        if created:
            contador += 1
            
    messages.success(request, f'{contador} vacinas padrão foram adicionadas!')
    return redirect('gerenciar_vacinas')


@login_required
def dashboard_quimicos(request):
    empresa = request.user.perfil.empresa
    produtos = ProdutoQuimico.objects.filter(empresa=empresa)
    
    termo = request.GET.get('busca')
    if termo:
        produtos = produtos.filter(
            Q(nome__icontains=termo) | Q(cas_number__icontains=termo)
        )

    exposicoes = ExposicaoOcupacional.objects.filter(empresa=empresa).select_related('funcionario', 'produto_quimico', 'funcionario__setor')
    
    setores_risco = []
    setores = Setor.objects.filter(empresa=empresa)
    for setor in setores:
        prods_setor = produtos.filter(setor=setor)
        funcionarios_setor = Funcionario.objects.filter(setor=setor).count()
        qtd_produtos = prods_setor.count()
        nivel = 'baixo'
        if qtd_produtos > 10: nivel = 'alto'
        elif qtd_produtos > 5: nivel = 'medio'
        
        riscos_setor = set()
        for p in prods_setor:
            riscos_setor.update(p.lista_ghs)
            
        if qtd_produtos > 0:
            setores_risco.append({
                'nome': setor.nome,
                'nivel': nivel,
                'produtos': qtd_produtos,
                'funcionarios': funcionarios_setor,
                'principais_riscos': list(riscos_setor)[:3]
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
def api_lista_quimicos(request):
    try:
        empresa = request.user.perfil.empresa
        produtos = ProdutoQuimico.objects.filter(empresa=empresa)
        serializer = ProdutoQuimicoSerializer(produtos, many=True)
        return Response(serializer.data)
    except AttributeError:
        return Response({"erro": "Usuário sem empresa vinculada"}, status=400)
    
@login_required
def lista_setores(request):
    empresa = request.user.perfil.empresa
    setores = Setor.objects.filter(empresa=empresa).order_by('nome')
    return render(request, 'setores/lista.html', {'setores': setores})

login_required
def novo_setor(request):
    empresa = request.user.perfil.empresa
    if request.method == 'POST':
        # ANTES ERA: form = SetorForm(empresa, request.POST) -> ISSO DAVA ERRO
        # CORRETO:
        form = SetorForm(request.POST) 
        if form.is_valid():
            setor = form.save(commit=False)
            setor.empresa = empresa
            setor.save()
            return redirect('lista_setores')
    else:
        # ANTES ERA: form = SetorForm(empresa)
        # CORRETO:
        form = SetorForm()
    return render(request, 'generic_form.html', {'form': form, 'titulo': 'Novo Setor'})

@login_required
def editar_setor(request, id):
    empresa = request.user.perfil.empresa
    setor = get_object_or_404(Setor, pk=id, empresa=empresa)
    
    if request.method == 'POST':
        # CORRETO (Sem 'empresa'):
        form = SetorForm(request.POST, instance=setor)
        if form.is_valid():
            form.save()
            return redirect('lista_setores')
    else:
        # CORRETO (Sem 'empresa'):
        form = SetorForm(instance=setor)
    return render(request, 'generic_form.html', {'form': form, 'titulo': f'Editar: {setor.nome}'})

@login_required
def deletar_setor(request, id):
    empresa = request.user.perfil.empresa
    setor = get_object_or_404(Setor, pk=id, empresa=empresa)
    if request.method == 'POST':
        try:
            setor.delete()
        except ProtectedError:
            pass
        return redirect('lista_setores')
    return render(request, 'confirmar_delete.html', {'objeto': setor})

@login_required
def registrar_exame(request, func_id):
    empresa = request.user.perfil.empresa
    funcionario = get_object_or_404(Funcionario, pk=func_id, empresa=empresa)
    if request.method == 'POST':
        form = ExameForm(request.POST, request.FILES)
        if form.is_valid():
            exame = form.save(commit=False)
            exame.funcionario = funcionario
            exame.empresa = empresa
            exame.save()
    return redirect('detalhe_funcionario', id=func_id)

@login_required
def deletar_exame(request, exame_id):
    empresa = request.user.perfil.empresa
    exame = get_object_or_404(Exame, pk=exame_id, empresa=empresa)
    func_id = exame.funcionario.id
    exame.delete()
    return redirect('detalhe_funcionario', id=func_id)

@login_required
def editar_exame(request, exame_id):
    empresa = request.user.perfil.empresa
    exame = get_object_or_404(Exame, pk=exame_id, empresa=empresa)
    funcionario_id = exame.funcionario.id
    if request.method == 'POST':
        form = ExameForm(request.POST, request.FILES, instance=exame)
        if form.is_valid():
            form.save()
            return redirect('detalhe_funcionario', id=funcionario_id)
    return redirect('detalhe_funcionario', id=funcionario_id)

# --- PMOC (AR CONDICIONADO) ---
@login_required
def lista_pmoc(request):
    base_qs = ArCondicionado.objects.filter(empresa=request.user.perfil.empresa)
    busca = request.GET.get('busca')
    status = request.GET.get('status')
    itens = base_qs
    if busca:
        itens = itens.filter(Q(nome__icontains=busca) | Q(codigo__icontains=busca))
    if status and status != 'todos':
        itens = itens.filter(status=status)
    
    stats = {
        'total': base_qs.count(),
        'ativos': base_qs.filter(status='ativo').count(),
        'manutencao': base_qs.filter(status='manutencao').count(),
        'inativos': base_qs.filter(status='inativo').count(),
    }
    return render(request, 'pmoc/lista.html', {'itens': itens, 'stats': stats})

@login_required
def novo_pmoc(request):
    if request.method == 'POST':
        form = ArCondicionadoForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.user.perfil.empresa
            obj.save()
            return redirect('lista_pmoc')
    else:
        form = ArCondicionadoForm()
    return render(request, 'pmoc/form.html', {'form': form})

# --- NR-13 (CALDEIRAS) ---
@login_required
def lista_nr13(request):
    base_qs = EquipamentoNR13.objects.filter(empresa=request.user.perfil.empresa)
    busca = request.GET.get('busca')
    status = request.GET.get('status')
    itens = base_qs
    if busca:
        itens = itens.filter(Q(nome__icontains=busca) | Q(codigo__icontains=busca))
    if status and status != 'todos':
        itens = itens.filter(status=status)
    
    stats = {
        'total': base_qs.count(),
        'ativos': base_qs.filter(status='ativo').count(),
        'manutencao': base_qs.filter(status='manutencao').count(),
        'inativos': base_qs.filter(status='inativo').count(),
    }
    return render(request, 'nr13/lista.html', {'itens': itens, 'stats': stats})

@login_required
def novo_nr13(request):
    if request.method == 'POST':
        form = EquipamentoNR13Form(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.user.perfil.empresa
            obj.save()
            return redirect('lista_nr13')
    else:
        form = EquipamentoNR13Form()
    return render(request, 'nr13/form.html', {'form': form})

# --- MATRIZ SST E ESTRUTURA (SETOR/CARGO) ---

@login_required
def configurar_matriz_sst(request):
    empresa = request.user.perfil.empresa
    
    if request.method == 'POST' and 'matriz_submit' in request.POST:
        form = MatrizRiscoEPIForm(empresa.id, request.POST)
        if form.is_valid():
            setor = form.cleaned_data['setor']
            cargo = form.cleaned_data['cargo']
            
            # Tenta buscar uma matriz existente ou cria uma nova
            matriz, created = MatrizRiscoEPI.objects.get_or_create(
                empresa=empresa, setor=setor, cargo=cargo
            )
            
            # --- LÓGICA DE HERANÇA (Só executa se acabou de criar o vínculo) ---
            if created:
                # Copia os dados GLOBAIS do Setor para o Cargo específico
                if setor.riscos.exists():
                    matriz.riscos.add(*setor.riscos.all())
                
                if setor.epis.exists():
                    matriz.epis_obrigatorios.add(*setor.epis.all())

                if setor.normas.exists():
                    matriz.nrs.add(*setor.normas.all())
                
                if setor.vacinas.exists():
                    matriz.vacinas.add(*setor.vacinas.all())

                if setor.exames.exists():
                    matriz.exames.add(*setor.exames.all())

                # Salva a primeira versão com a herança
                matriz.save()

            # --- AGORA APLICA O QUE VEIO DO FORMULÁRIO (ESPECÍFICOS DO CARGO) ---
            # O formulário da view 'MatrizRiscoEPIForm' vai salvar por cima.
            # Como é um ManyToMany, o form.save() normalmente substitui tudo.
            # Para manter a herança + novos, precisamos de cuidado.
            
            # Neste caso, o form do Wizard já traz os itens selecionados pelo usuário.
            # Se o usuário não selecionou nada no Wizard (passou rápido), o form vai salvar vazio.
            # Porém, a estratégia ideal aqui é:
            # 1. O usuário cria o vínculo.
            # 2. O sistema herda.
            # 3. O usuário edita para adicionar os específicos.
            
            # ATUALIZAÇÃO DO FORM PARA NÃO PERDER HERANÇA:
            # Como o form save() do Django limpa e seta os novos valores, se quisermos
            # SOMAR (Herança + Form), temos que fazer manual ou garantir que o form já venha preenchido.
            
            # Vamos salvar o form normalmente (o que o usuário marcou no modal conta como "final")
            # SE você quiser que o modal JÁ VENHA PREENCHIDO com os dados do setor, 
            # isso teria que ser feito via JavaScript no Frontend (mais complexo).
            
            # Abordagem Híbrida Simples (Backend):
            # Salva o form. Se foi criação, adicionamos o que faltou do setor.
            obj_salvo = form.save(commit=False)
            obj_salvo.pk = matriz.pk # Garante que estamos editando o objeto criado/recuperado
            form.save_m2m() # Salva o que o usuário marcou no modal
            
            if created:
                # Reforça a herança: Adiciona o do setor (sem remover o que o usuário marcou)
                matriz.riscos.add(*setor.riscos.all())
                matriz.epis_obrigatorios.add(*setor.epis.all())
                matriz.nrs.add(*setor.normas.all())
                matriz.vacinas.add(*setor.vacinas.all())
                matriz.exames.add(*setor.exames.all())
            
            messages.success(request, 'Matriz atualizada com sucesso! (Dados do setor herdados)')
            return redirect('configurar_matriz_sst')
        else:
            messages.error(request, 'Erro ao salvar. Verifique os campos.')
    
    # ... resto da view (contexto, render, etc)
    # ATENÇÃO: Atualize a instanciação dos forms auxiliares para passar a empresa
    regras = MatrizRiscoEPI.objects.filter(empresa=empresa).select_related('setor', 'cargo')
    
    return render(request, 'configuracoes/matriz_sst.html', {
        'regras': regras,
        'setores': Setor.objects.filter(empresa=empresa),
        'cargos': Cargo.objects.filter(empresa=empresa),
        'form': MatrizRiscoEPIForm(empresa.id),
        'form_setor': SetorForm(empresa=empresa), # Atualizado aqui
        'form': MatrizRiscoEPIForm(empresa.id),
        'form_cargo': CargoForm(),
    })

# --- APIs PARA A MATRIZ E CADASTRO (JSON) ---

@login_required
def api_consulta_matriz(request):
    setor_id = request.GET.get('setor_id')
    cargo_texto = request.GET.get('cargo')
    empresa = request.user.perfil.empresa

    if not setor_id or not cargo_texto:
        return JsonResponse({'encontrado': False})

    try:
        cargo_obj = Cargo.objects.filter(empresa=empresa, nome__iexact=cargo_texto).first()
        if not cargo_obj:
            return JsonResponse({'encontrado': False, 'msg': 'Cargo não cadastrado na estrutura.'})

        matriz = MatrizRiscoEPI.objects.filter(
            empresa=empresa, setor_id=setor_id, cargo=cargo_obj
        ).first()

        if matriz:
            return JsonResponse({
                'encontrado': True,
                'riscos': [f"{r.get_tipo_display()}: {r.agente}" for r in matriz.riscos.all()],
                'epis': [e.nome for e in matriz.epis_obrigatorios.all()],
                'nrs': [nr.codigo for nr in matriz.nrs.all()],
                'vacinas': [v.nome for v in matriz.vacinas.all()],
                'exames': [f"{e.nome} (TUSS: {e.codigo_tuss})" for e in matriz.exames.all()]
            })
    except Exception as e:
        return JsonResponse({'encontrado': False, 'error': str(e)})
    
    return JsonResponse({'encontrado': False})

@login_required
def api_gerenciar_estrutura(request, tipo):
    empresa = request.user.perfil.empresa
    
    if request.method == 'POST':
        try:
            if tipo == 'setor':
                # CORREÇÃO 1: Passar 'empresa=empresa' para carregar as opções corretas
                form = SetorForm(request.POST, empresa=empresa)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.empresa = empresa
                    obj.save()
                    # CORREÇÃO 2: Salvar os relacionamentos (Riscos, EPIs, etc)
                    form.save_m2m()
                    return JsonResponse({'success': True, 'id': obj.id, 'nome': obj.nome})
                else:
                    # Retorna os erros para ajudar no debug
                    return JsonResponse({'success': False, 'error': form.errors.as_json()})
            
            elif tipo == 'cargo':
                form = CargoForm(request.POST)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.empresa = empresa
                    obj.save()
                    return JsonResponse({'success': True, 'id': obj.id, 'nome': obj.nome})
                else:
                    return JsonResponse({'success': False, 'error': form.errors.as_json()})
                    
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            obj_id = data.get('id')
            if tipo == 'setor':
                Setor.objects.filter(id=obj_id, empresa=empresa).delete()
            elif tipo == 'cargo':
                Cargo.objects.filter(id=obj_id, empresa=empresa).delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False})

@login_required
def api_criar_tipo_exame(request):
    if request.method == "POST":
        from .forms import TipoExameForm 
        form = TipoExameForm(request.POST)
        if form.is_valid():
            exame = form.save(commit=False)
            exame.empresa = request.user.perfil.empresa
            exame.save()
            return JsonResponse({'success': True, 'id': exame.id, 'nome': str(exame)})
    return JsonResponse({'success': False})

# Views placeholder para completar imports do urls.py (se faltar alguma)
@login_required
def deletar_quimico(request, pk): return redirect('dashboard_quimicos')
@login_required
def deletar_risco(request, id): return redirect('dashboard_quimicos')
@login_required
def lista_advertencias(request): return redirect('dashboard')

@login_required
def novo_quimico(request):
    empresa = request.user.perfil.empresa
    if request.method == 'POST':
        form = ProdutoQuimicoForm(empresa.id, request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            return redirect('dashboard_quimicos')
    else:
        form = ProdutoQuimicoForm(empresa.id)
    return render(request, 'generic_form.html', {'form': form, 'titulo': 'Novo Produto Químico'})

@login_required
def editar_quimico(request, id):
    empresa = request.user.perfil.empresa
    prod = get_object_or_404(ProdutoQuimico, pk=id, empresa=empresa)
    if request.method == 'POST':
        form = ProdutoQuimicoForm(empresa.id, request.POST, request.FILES, instance=prod)
        if form.is_valid():
            form.save()
            return redirect('dashboard_quimicos')
    else:
        form = ProdutoQuimicoForm(empresa.id, instance=prod)
    return render(request, 'generic_form.html', {'form': form, 'titulo': 'Editar Químico'})

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
def associar_risco_setor(request, setor_id):
    empresa = request.user.perfil.empresa
    setor = get_object_or_404(Setor, pk=setor_id, empresa=empresa)
    
    if request.method == 'POST':
        riscos_ids = request.POST.getlist('riscos')
        setor.riscos.clear()
        for r_id in riscos_ids:
            r = get_object_or_404(RiscoOcupacional, pk=r_id, empresa=empresa)
            setor.riscos.add(r)
        setor.save()
        
    return redirect('dashboard_quimicos')


@login_required
def config_hospitais(request):
    empresa = request.user.perfil.empresa
    tipos = TipoEspecialidade.objects.filter(empresa=empresa)
    form = TipoEspecialidadeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.empresa = empresa
        obj.save()
        return redirect('config_hospitais')
    return render(request, 'hospitais/gerenciar_especialidades.html', {'tipos': tipos, 'form': form})

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
            return redirect('dashboard_hospitais')
    else:
        form = HospitalForm(empresa.id)
    return render(request, 'hospitais/form.html', {'form': form})



#### PGR

@login_required
def pgr_empresa(request):
    empresa = request.user.perfil.empresa
    
    # 1. Buscamos todos os setores da empresa
    setores = Setor.objects.filter(empresa=empresa).order_by('nome')
    
    dados_pgr = []

    for setor in setores:
        # 2. Para cada setor, buscamos as Matrizes de Risco configuradas (que ligam Setor a Cargo)
        matrizes = MatrizRiscoEPI.objects.filter(
            empresa=empresa, 
            setor=setor
        ).select_related('cargo').prefetch_related(
            'riscos', 
            'epis_obrigatorios', 
            'exames', 
            'vacinas'
        )

        # Se houver cargos configurados neste setor, processamos
        if matrizes.exists():
            cargos_do_setor = []
            
            for matriz in matrizes:
                # Agrupamos os dados por Cargo dentro do Setor
                cargos_do_setor.append({
                    'cargo_nome': matriz.cargo.nome,
                    'descricao_cargo': matriz.cargo.descricao,
                    'riscos': matriz.riscos.all(),
                    'epis': matriz.epis_obrigatorios.all(),
                    'exames': matriz.exames.all(),
                    'vacinas': matriz.vacinas.all(),
                    'nrs': matriz.nrs.all()
                })
            
            dados_pgr.append({
                'setor_nome': setor.nome,
                'descricao_setor': setor.descricao,
                'cargos': cargos_do_setor
            })

    context = {
        'dados_pgr': dados_pgr,
        'empresa': empresa,
        'data_emissao': date.today()
    }

    return render(request, 'pgr_empresa.html', context)


@login_required
def popular_padroes_usuario(request):
    """
    Função de emergência para popular EPIs e Riscos para a empresa do usuário logado.
    Acesse via navegador: /popular-padroes/
    """
    empresa = request.user.perfil.empresa
    
    # 1. EPIs
    from core.models import CategoriaEPI, TipoEPI
    dados_epi = {
        'Proteção da Cabeça': ['Capacete de segurança', 'Capuz ou balaclava'],
        'Proteção Auditiva': ['Protetor tipo concha', 'Protetor tipo plug'],
        'Proteção Respiratória': ['Máscara PFF1', 'Máscara PFF2', 'Máscara Facial'],
        'Proteção Visual': ['Óculos incolor', 'Óculos escuro', 'Protetor facial'],
        'Proteção Mãos': ['Luva vaqueta', 'Luva nitrílica', 'Luva malha', 'Luva PVC'],
        'Proteção Pés': ['Botina biqueira aço', 'Botina composite', 'Bota PVC'],
        'Proteção Corpo': ['Avental raspa', 'Capa chuva', 'Colete reflexivo'],
        'Altura': ['Cinto paraquedista', 'Talabarte Y', 'Trava-quedas']
    }
    
    count = 0
    for cat_nome, tipos in dados_epi.items():
        # Garante a categoria
        CategoriaEPI.objects.get_or_create(empresa=empresa, nome=cat_nome)
        # Garante os tipos
        for tipo in tipos:
            _, created = TipoEPI.objects.get_or_create(empresa=empresa, nome=tipo)
            if created: count += 1
            
    return JsonResponse({'status': 'ok', 'mensagem': f'{count} EPIs criados/verificados para a empresa {empresa.nome_fantasia}!'})


def load_tipos_epi(request):
    categoria_id = request.GET.get('categoria')
    tipos = TipoEPI.objects.none()
    
    if categoria_id:
        tipos = TipoEPI.objects.filter(categoria_id=categoria_id).order_by('nome')
    
    return render(request, 'partials/epis_dropdown_list.html', {'tipos': tipos})