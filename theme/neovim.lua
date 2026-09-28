-- Phantom Thieves colourscheme for Neovim/LazyVim.
-- Defined inline rather than pulled from a marketplace plugin, so the theme has
-- no third-party colourscheme dependency.
local c = {
  bg = "#0a0a0a",
  dark = "#050505",
  light = "#1b1b1b",
  fg = "#f2f2f2",
  dim = "#5c5c5c",
  lfg = "#cfcfcf",
  red = "#e60012",
  bred = "#ff4a52",
  pink = "#ff5c8a",
  gold = "#ffc72c",
  cyan = "#4ec9c9",
  blue = "#5f72d8",
  green = "#6fbf6b",
  orange = "#ff7a1a",
  brown = "#9c6b52",
  sel = "#2b0a0e",
}

local hl = vim.api.nvim_set_hl
local none = "NONE"

hl(0, "Normal", { fg = c.fg, bg = c.bg })
hl(0, "NormalNC", { fg = c.fg, bg = c.bg })
hl(0, "NormalFloat", { fg = c.fg, bg = c.light })
hl(0, "FloatBorder", { fg = c.red, bg = c.light })
hl(0, "FloatTitle", { fg = c.red, bg = c.light, bold = true })
hl(0, "ColorColumn", { bg = c.light })
hl(0, "Cursor", { fg = c.bg, bg = c.red })
hl(0, "lCursor", { fg = c.bg, bg = c.red })
hl(0, "TermCursor", { fg = c.bg, bg = c.red })
hl(0, "TermCursorNC", { fg = c.bg, bg = c.dim })

hl(0, "Comment", { fg = c.dim, italic = true })
hl(0, "SpecialComment", { fg = c.dim, bold = true, italic = true })
hl(0, "Constant", { fg = c.gold })
hl(0, "String", { fg = c.pink })
hl(0, "Character", { fg = c.pink })
hl(0, "Number", { fg = c.gold })
hl(0, "Boolean", { fg = c.gold })
hl(0, "Float", { fg = c.gold })

hl(0, "Identifier", { fg = c.lfg })
hl(0, "Function", { fg = c.red, bold = true })
hl(0, "Statement", { fg = c.red, bold = true })
hl(0, "Conditional", { fg = c.red })
hl(0, "Repeat", { fg = c.red })
hl(0, "Label", { fg = c.red })
hl(0, "Operator", { fg = c.red })
hl(0, "Keyword", { fg = c.red, bold = true })
hl(0, "Exception", { fg = c.red, bold = true })
hl(0, "PreProc", { fg = c.orange })
hl(0, "Include", { fg = c.orange })
hl(0, "Define", { fg = c.orange })
hl(0, "Macro", { fg = c.orange })
hl(0, "PreCondit", { fg = c.orange })

hl(0, "Type", { fg = c.cyan })
hl(0, "Structure", { fg = c.cyan })
hl(0, "Class", { fg = c.cyan, bold = true })
hl(0, "Special", { fg = c.blue })
hl(0, "SpecialChar", { fg = c.blue })
hl(0, "Tag", { fg = c.pink })
hl(0, "Delimiter", { fg = c.lfg })
hl(0, "Debug", { fg = c.pink })

hl(0, "Error", { fg = c.bred })
hl(0, "Todo", { fg = c.bg, bg = c.gold, bold = true })
hl(0, "WarningMsg", { fg = c.gold })
hl(0, "MoreMsg", { fg = c.cyan })
hl(0, "ModeMsg", { fg = c.lfg })
hl(0, "Question", { fg = c.cyan })

hl(0, "Visual", { bg = c.sel })
hl(0, "VisualNOS", { bg = c.sel })
hl(0, "Selection", { bg = c.sel })
hl(0, "Search", { fg = c.bg, bg = c.gold })
hl(0, "IncSearch", { fg = c.bg, bg = c.bred, bold = true })
hl(0, "CurSearch", { fg = c.bg, bg = c.orange })
hl(0, "Substitute", { fg = c.bg, bg = c.pink })
hl(0, "LineNr", { fg = c.dim })
hl(0, "CursorLine", { bg = c.light })
hl(0, "CursorLineNr", { fg = c.red, bold = true })
hl(0, "SignColumn", { bg = none, fg = c.dim })
hl(0, "FoldColumn", { bg = none, fg = c.dim })
hl(0, "Folded", { fg = c.dim, bg = c.light })
hl(0, "SignColumnSB", { bg = none, fg = c.dim })
hl(0, "Whitespace", { fg = c.dim })
hl(0, "SpecialKey", { fg = c.dim })
hl(0, "NonText", { fg = c.dim })
hl(0, "EndOfBuffer", { fg = c.dark })

hl(0, "StatusLine", { fg = c.lfg, bg = c.dark })
hl(0, "StatusLineNC", { fg = c.dim, bg = c.dark })
hl(0, "VertSplit", { fg = c.dim })
hl(0, "WinSeparator", { fg = c.red })

hl(0, "Pmenu", { fg = c.lfg, bg = c.light })
hl(0, "PmenuSel", { bg = c.sel, bold = true })
hl(0, "PmenuSbar", { bg = c.dark })
hl(0, "PmenuThumb", { bg = c.red })
hl(0, "PmenuKind", { fg = c.cyan, bg = c.light })
hl(0, "PmenuExtra", { fg = c.dim, bg = c.light })
hl(0, "PmenuMatch", { fg = c.red, bg = c.light, bold = true })
hl(0, "PmenuMatchSel", { fg = c.red, bg = c.sel, bold = true })

hl(0, "Directory", { fg = c.pink })
hl(0, "Title", { fg = c.red, bold = true })
hl(0, "Conceal", { fg = c.dim })
hl(0, "Italic", { italic = true })
hl(0, "Bold", { bold = true })

hl(0, "DiffAdd", { bg = "#1d3016" })
hl(0, "DiffChange", { bg = "#33240a" })
hl(0, "DiffDelete", { bg = "#331013" })
hl(0, "DiffText", { bg = c.red })
hl(0, "Added", { fg = c.green })
hl(0, "Changed", { fg = c.gold })
hl(0, "Removed", { fg = c.bred })

hl(0, "DiagnosticError", { fg = c.bred })
hl(0, "DiagnosticWarn", { fg = c.gold })
hl(0, "DiagnosticInfo", { fg = c.cyan })
hl(0, "DiagnosticHint", { fg = c.lfg })
hl(0, "DiagnosticOk", { fg = c.green })
hl(0, "DiagnosticVirtualTextError", { fg = c.bred, bg = c.dark })
hl(0, "DiagnosticVirtualTextWarn", { fg = c.gold, bg = c.dark })
hl(0, "DiagnosticVirtualTextInfo", { fg = c.cyan, bg = c.dark })
hl(0, "DiagnosticVirtualTextHint", { fg = c.lfg, bg = c.dark })
hl(0, "DiagnosticUnderlineError", { sp = c.bred, underline = true })
hl(0, "DiagnosticUnderlineWarn", { sp = c.gold, underline = true })
hl(0, "DiagnosticUnderlineInfo", { sp = c.cyan, underline = true })
hl(0, "DiagnosticUnderlineHint", { sp = c.lfg, underline = true })
hl(0, "DiagnosticFloatingError", { fg = c.bred, bg = c.light })
hl(0, "DiagnosticFloatingWarn", { fg = c.gold, bg = c.light })
hl(0, "DiagnosticFloatingInfo", { fg = c.cyan, bg = c.light })
hl(0, "DiagnosticFloatingHint", { fg = c.lfg, bg = c.light })
hl(0, "DiagnosticSignError", { fg = c.bred })
hl(0, "DiagnosticSignWarn", { fg = c.gold })
hl(0, "DiagnosticSignInfo", { fg = c.cyan })
hl(0, "DiagnosticSignHint", { fg = c.lfg })

hl(0, "SpellBad", { sp = c.bred, undercurl = true })
hl(0, "SpellLocal", { sp = c.cyan, undercurl = true })
hl(0, "SpellCap", { sp = c.gold, undercurl = true })

hl(0, "MatchParen", { fg = c.gold, bg = c.light, bold = true })
hl(0, "MiniCmd", { fg = c.bg, bg = c.gold, bold = true })
hl(0, "VisualNOSpace", { bg = none })
hl(0, "QuickFixLine", { bg = c.sel, bold = true })
hl(0, "QuickFixText", { fg = c.lfg })
hl(0, "@lsp.type.class.typescript", { link = "Type" })
hl(0, "@lsp.type.function.typescript", { link = "Function" })
hl(0, "@lsp.type.variable.typescript", { link = "Identifier" })
hl(0, "@variable.member", { fg = c.cyan })
hl(0, "@variable.parameter", { fg = c.lfg, italic = true })
hl(0, "@punctuation.delimiter", { fg = c.dim })
hl(0, "TSPunctDelimiter", { fg = c.dim })
hl(0, "TSField", { fg = c.lfg })
hl(0, "TSProperty", { fg = c.cyan })

vim.g.colors_name = "phantom-thieves"

return {
  {
    "LazyVim/LazyVim",
    opts = { colorscheme = "phantom-thieves" },
  },
}
