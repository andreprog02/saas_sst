# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import CadastroSaaSForm, FuncionarioForm, SetorForm, TipoEPIForm, LocalizacaoForm, EPIForm
from .models import Funcionario, Setor, TipoEPI, Localizacao, EPI

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
    if not hasattr(request.user, 'perfil'):
        return redirect('cadastro')
    empresa = request.user.perfil.empresa
    return render(request, 'dashboard.html', {'empresa': empresa})

@login_required
def lista_funcionarios(request):
    empresa_logada = request.user.perfil.empresa
    funcionarios = Funcionario.objects.filter(empresa=empresa_logada)
    return render(request, 'funcionarios_lista.html', {'funcionarios': funcionarios})

@login_required
def criar_setor(request):
    if request.method == 'POST':
        form = SetorForm(request.POST)
        if form.is_valid():
            setor = form.save(commit=False)
            setor.empresa = request.user.perfil.empresa
            setor.save()
            return redirect('dashboard')
    else:
        form = SetorForm()
    return render(request, 'setor_form.html', {'form': form})

@login_required
def criar_funcionario(request):
    empresa_id = request.user.perfil.empresa.id
    if request.method == 'POST':
        form = FuncionarioForm(empresa_id, request.POST)
        if form.is_valid():
            funcionario = form.save(commit=False)
            funcionario.empresa = request.user.perfil.empresa 
            funcionario.save()
            return redirect('lista_funcionarios')
    else:
        form = FuncionarioForm(empresa_id)
    return render(request, 'funcionario_form.html', {'form': form})

# --- NOVAS VIEWS (CRUD EPIs) ---

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
    return render(request, 'confirmar_delete.html', {'obj': epi})