-- Phantom Thieves: Hyprland overrides.
--
-- This file is re-read on every theme change (default/hypr/omarchy.lua requires
-- omarchy.current.theme.hyprland after the Omarchy defaults, and `omarchy
-- theme set` runs `hyprctl reload`), so everything here arrives with the theme
-- and leaves with it. Your own ~/.config/hypr/looknfeel.lua is loaded after
-- this, so it still wins.

-- One red, one pink, no neon. The gradient runs the short way so the crimson
-- sits on one edge and the Panther pink on the other, which reads as a hard
-- two-tone cut rather than a soft blend -- the way Persona 5's panels do.
local active_border_color = {
  colors = { "rgba(e60012ff)", "rgba(ff2b45ff)", "rgba(ff5c8aff)" },
  angle = 135,
}
local inactive_border_color = "rgba(7d384188)"
local active_shadow_color = "rgba(e6001299)"
local inactive_shadow_color = "rgba(7d38414d)"

hl.config({
  general = {
    col = {
      active_border = active_border_color,
      inactive_border = inactive_border_color,
    },
  },

  group = {
    col = {
      border_active = active_border_color,
      border_inactive = inactive_border_color,
    },
  },

  decoration = {
    shadow = {
      enabled = true,
      range = 8,
      render_power = 4,
      color = active_shadow_color,
      color_inactive = inactive_shadow_color,
    },
  },
})

-- Persona 5 motion: it never eases in gently. Everything decelerates hard and
-- arrives early, and windows arrive as a punch rather than a fade. The
-- `workspaces` leaf is left alone -- your looknfeel.lua sets it, and loads
-- after this file.
hl.curve("phantomSnap", { type = "bezier", points = { { 0.12, 1 }, { 0.22, 1 } } })
hl.curve("phantomEase", { type = "bezier", points = { { 0.66, 0 }, { 0.84, 0 } } })
hl.curve("phantomCut", { type = "bezier", points = { { 0.05, 0.9 }, { 0.15, 1 } } })

hl.animation({ leaf = "global", enabled = true, speed = 15, bezier = "phantomSnap" })
hl.animation({ leaf = "border", enabled = true, speed = 8, bezier = "phantomSnap" })
hl.animation({ leaf = "windows", enabled = true, speed = 5, bezier = "phantomSnap" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 6, bezier = "phantomEase", style = "popin 80%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 5.5, bezier = "phantomEase", style = "popin 80%" })
hl.animation({ leaf = "layers", enabled = true, speed = 4, bezier = "phantomCut" })
hl.animation({ leaf = "fade", enabled = true, speed = 2.2, bezier = "phantomSnap" })
