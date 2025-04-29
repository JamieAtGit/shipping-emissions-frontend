import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './app.css'
import EstimateForm from './EstimateForm.jsx'

//import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <EstimateForm /> 
  </StrictMode>,
)

//was app instead of estimateform