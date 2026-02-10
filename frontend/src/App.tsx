import { Routes, Route } from 'react-router-dom'

// Lazy load feature pages
import { NewsFormPage } from './features/news/pages/NewsFormPage'

function App() {
  return (
    <div className="min-h-screen bg-background">
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/admin/news/new" element={<NewsFormPage />} />
        {/* [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-FE-T01] */}
        <Route path="/admin/news/:id/edit" element={<NewsFormPage />} />
      </Routes>
    </div>
  )
}

// Temporary home page
function HomePage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold text-foreground">
        Bienvenido
      </h1>
      <p className="mt-4 text-muted-foreground">
        Sistema de gestión de noticias
      </p>
      <a
        href="/admin/news/new"
        className="mt-4 inline-block text-primary underline"
      >
        Crear nueva noticia →
      </a>
    </div>
  )
}

export default App
