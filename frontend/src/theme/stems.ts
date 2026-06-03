// AI-assisted: Stem track styles — orange waveform depth on sandy neumorphic base.

export const STEM_TRACK_STYLES = {
  vocals: { label: 'Vocals', waveOpacity: 1 },
  drums: { label: 'Drums', waveOpacity: 0.72 },
  bass: { label: 'Bass', waveOpacity: 0.88 },
  other: { label: 'Other', waveOpacity: 0.8 },
} as const

export type StemTrackId = keyof typeof STEM_TRACK_STYLES

export const STEM_TRACK_ORDER: StemTrackId[] = ['vocals', 'drums', 'bass', 'other']

export const ORANGE = {
  primary: '#e85d04',
  soft: '#f48c06',
} as const
