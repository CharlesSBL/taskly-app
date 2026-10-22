import { ApplicationHeader } from './components/ApplicationHeader'
import { TodosPage } from './features/todos'

export default function App() {
  return (
    <div>
      <ApplicationHeader />
      <TodosPage />
    </div>
  )
}
