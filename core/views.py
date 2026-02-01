# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
# AQUI ESTAVA O ERRO: Adicione SetorForm e SetorForm
from .forms import CadastroSaaSForm, FuncionarioForm, SetorForm 
# Importe também o modelo Setor para usar nos filtros depois
from .models import Funcionario, Setor


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
    # Garante que o usuário tem um perfil/empresa antes de acessar
    if not hasattr(request.user, 'perfil'):
        return redirect('cadastro') # Ou outra lógica de segurança
        
    empresa = request.user.perfil.empresa
    return render(request, 'dashboard.html', {'empresa': empresa})

@login_required
def lista_funcionarios(request):
    # Recupera a empresa do usuário logado
    empresa_logada = request.user.perfil.empresa
    # Filtra: traz só funcionários desta empresa
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
            return redirect('dashboard') # Ou uma lista de setores se preferir
    else:
        form = SetorForm()
    return render(request, 'setor_form.html', {'form': form})

@login_required
def criar_funcionario(request):
    empresa_id = request.user.perfil.empresa.id
    
    if request.method == 'POST':
        # Passamos o empresa_id para o formulário filtrar o dropdown
        form = FuncionarioForm(empresa_id, request.POST)
        if form.is_valid():
            funcionario = form.save(commit=False)
            funcionario.empresa = request.user.perfil.empresa 
            funcionario.save()
            return redirect('lista_funcionarios')
    else:
        form = FuncionarioForm(empresa_id) # Passamos o ID aqui também
    
    return render(request, 'funcionario_form.html', {'form': form})