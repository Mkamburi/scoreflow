// AI-assisted: Editor toolbar — neumorphic undo/redo controls.

interface EditorToolbarProps {
  canUndo: boolean
  canRedo: boolean
  onUndo: () => void
  onRedo: () => void
  isEditorActive: boolean
}

export function EditorToolbar({
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  isEditorActive,
}: EditorToolbarProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 className="sf-heading text-lg">Edit score</h2>
        <p className="sf-text-muted mt-1 text-sm">
          {isEditorActive
            ? 'Click notes to edit pitch and duration. Use the toolbar inside the editor or undo below.'
            : 'Configure Flat.io to enable in-browser editing.'}
        </p>
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          aria-label="Undo"
          disabled={!canUndo}
          onClick={onUndo}
          className="sf-btn-ghost px-3 py-1.5 text-sm disabled:opacity-40"
        >
          Undo
        </button>
        <button
          type="button"
          aria-label="Redo"
          disabled={!canRedo}
          onClick={onRedo}
          className="sf-btn-ghost px-3 py-1.5 text-sm disabled:opacity-40"
        >
          Redo
        </button>
      </div>
    </div>
  )
}
