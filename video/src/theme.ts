// Colours and geometry measured from assets/subjects-offered/poster.png.
// All coordinates are poster pixels on the 1080x1440 canvas.

export const W = 1080;
export const H = 1440;
export const FPS = 30;
export const DURATION = 900;

export const C = {
  navy: "#002866", // table and cell fill
  royal: "#2E68B2", // frame and cell borders
  cellBorder: "#2A63AD",
  cyan: "#3BBEEC", // glossy rim highlight, column dividers
  divider: "#2FA3D8",
  deep: "#081027", // darkest background corner
  white: "#FFFFFF",
  red: "#970C10", // "Available for all levels:"
  bullet: "#154B98",
  contact: "#02165C",
  titleShadow: "#0F1B42",
};

export const FONT = "Outfit";

// Table
export const FRAME = { x0: 102, y0: 403, x1: 967, y1: 1210, r: 34, stroke: 6 };
export const COL = { subjX0: 131, subjX1: 396, midX1: 676, priceX1: 941 };
export const SUBJ_CX = 263.5;
export const MID_CX = 536;
export const PRICE_CX = 808;
export const ROW_TOP0 = 428;
export const ROW_PITCH = 48.07;
export const ROW_H = 38;
export const rowTop = (i: number) => ROW_TOP0 + ROW_PITCH * i;

export type Price = { amount: number; slash: string; mode: string; baseline: number };
export type Group = {
  rows: string[];
  firstRow: number;
  y0: number;
  y1: number;
  mid: { text: string; baseline: number }[];
  startingBaseline: number;
  prices: Price[];
};

// Each price line is "RM <amount><slash>month for" then the mode on the next line.
// Group 3 has no space before the slash on the poster ("RM 239/ month for").
export const GROUPS: Group[] = [
  {
    rows: ["Bahasa Melayu", "English", "Mathematics", "Science", "Sejarah"],
    firstRow: 0,
    y0: 428,
    y1: 658.5,
    mid: [
      { text: "Personal Tutoring", baseline: 508 },
      { text: "or", baseline: 548 },
      { text: "Group Tutoring", baseline: 588 },
    ],
    startingBaseline: 490,
    prices: [
      { amount: 50, slash: " / ", mode: "Group Tutoring", baseline: 530 },
      { amount: 130, slash: " / ", mode: "Personal Tutoring", baseline: 590 },
    ],
  },
  {
    rows: ["Additional Mathematics", "Physics", "Chemistry", "Biology"],
    firstRow: 5,
    y0: 668,
    y1: 851.5,
    mid: [
      { text: "Personal Tutoring", baseline: 725 },
      { text: "or", baseline: 765 },
      { text: "Group Tutoring", baseline: 805 },
    ],
    startingBaseline: 705,
    prices: [
      { amount: 90, slash: " / ", mode: "Group Tutoring", baseline: 745 },
      { amount: 239, slash: " / ", mode: "Personal Tutoring", baseline: 805 },
    ],
  },
  {
    rows: [
      "Computer Science",
      "Prinsip Perakaunan",
      "Perniagaan",
      "Ekonomi",
      "Geografi",
      "Sains Sukan",
      "Pendidikan Seni",
    ],
    firstRow: 9,
    y0: 860,
    y1: 1188,
    mid: [{ text: "Personal Tutoring only", baseline: 1030 }],
    startingBaseline: 986,
    prices: [{ amount: 239, slash: "/ ", mode: "Personal Tutoring", baseline: 1046 }],
  },
];

export const TUTOR_BOX = { x: 180, y: 140, w: 760, h: 264 };
// Name labels: two lines, centred, baselines measured on the poster.
export const TUTORS = [
  { id: "isaac", lines: ["Sir Isaac", "Guru Fizik"], cx: 521.5, baselines: [122, 137], wave: 0 },
  { id: "ashraf", lines: ["Cikgu Ashraf", "Guru Sejarah"], cx: 393, baselines: [136.5, 151.5], wave: 1 },
  { id: "natasha", lines: ["Cikgu Natasha", "Guru Bahasa Melayu"], cx: 673.5, baselines: [136.5, 151.5], wave: 1 },
  { id: "sharmila", lines: ["Teacher Sharmila", "English Teacher"], cx: 265.5, baselines: [167, 182], wave: 2 },
  { id: "claudia", lines: ["Cikgu Claudia", "Guru Seni"], cx: 814, baselines: [162.5, 177.5], wave: 2 },
] as const;
// Back to front.
export const TUTOR_DEPTH = ["sharmila", "claudia", "ashraf", "natasha", "isaac"] as const;

export const LOGO = { cx: 361, cy: 73, r: 38 };
