// AI-assisted: Milestone 3.5 score types — MusicXML is the single source of truth.

export type ScoreHistoryState = {
  musicXml: string | null
  canUndo: boolean
  canRedo: boolean
}

export const SCORE_HISTORY_LIMIT = 20
