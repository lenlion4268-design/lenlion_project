import { Component, type ErrorInfo, type ReactNode } from 'react'

type Props = { children: ReactNode }
type State = { error: string | null }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error: error.message }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('UI error:', error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="page">
          <h1>页面出错</h1>
          <p style={{ color: 'var(--danger)' }}>{this.state.error}</p>
        </div>
      )
    }
    return this.props.children
  }
}
