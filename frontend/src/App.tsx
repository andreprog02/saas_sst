import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import Funcionarios from "./pages/Funcionarios";
import FuncionarioProfile from "./pages/FuncionarioProfile";
import Empresas from "./pages/Empresas";
import EPIs from "./pages/EPIs";
import Extintores from "./pages/Extintores";
import ProdutosQuimicos from "./pages/ProdutosQuimicos";
import Hospitais from "./pages/Hospitais";
import Configuracoes from "./pages/Configuracoes";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/funcionarios" element={<Funcionarios />} />
            <Route path="/funcionarios/:id" element={<FuncionarioProfile />} />
            <Route path="/empresas" element={<Empresas />} />
            <Route path="/inventario/epis" element={<EPIs />} />
            <Route path="/inventario/extintores" element={<Extintores />} />
            <Route path="/inventario/equipamentos" element={<EPIs />} />
            
            {/* ESTA É A ROTA QUE VOCÊ QUER ACESSAR: */}
            <Route path="/inventario/quimicos" element={<ProdutosQuimicos />} />
            
            <Route path="/inventario/hospitais" element={<Hospitais />} />
            <Route path="/configuracoes" element={<Configuracoes />} />
            <Route path="/configuracoes/normas" element={<Configuracoes />} />
            <Route path="/configuracoes/notificacoes" element={<Configuracoes />} />
            <Route path="/configuracoes/sistema" element={<Configuracoes />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;