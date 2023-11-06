local M = {}

M.base_30 = {
  white = "#F8F8F2",
  darker_black = "#1f1e28",
  black = "#22212c", --  nvim bg
  black2 = "#2e2b3b",
  one_bg = "#373844", -- real bg of onedark
  one_bg2 = "#4b4c57",
  one_bg3 = "#5d5e68",
  grey = "#7a7a80",
  grey_fg = "#87878d",
  grey_fg2 = "#6e6f79",
  light_grey = "#73747e",
  red = "#ff9580",
  baby_pink = "#ff8dc5",
  pink = "#ff80bf",
  line = "#454158", -- for lines like vertsplit
  green = "#8aff80",
  vibrant_green = "#96ff8d",
  nord_blue = "#8b9bcd",
  blue = "#a1b1e3",
  yellow = "#ffff80",
  sun = "#ffff8d",
  purple = "#9580ff",
  dark_purple = "#8673e6",
  teal = "#92a2d4",
  orange = "#ffca80",
  cyan = "#80ffea",
  statusline_bg = "#2e2b3b",
  lightbg = "#545661",
  pmenu_bg = "#bb95f1",
  folder_bg = "#aa84e0",
}

M.base_16 = {
  base00 = "#22212c",
  base01 = "#383741",
  base02 = "#4e4d56",
  base03 = "#64646b",
  base04 = "#80ffea",
  base05 = "#f8f8f2",
  base06 = "#f1f1f8",
  base07 = "#f7f7fb",
  base08 = "#9580ff",
  base09 = "#ffca80",
  base0A = "#80ffea",
  base0B = "#ffff80",
  base0C = "#8be9fd",
  base0D = "#8aff80",
  base0E = "#ff80bf",
  base0F = "#f8f8f2",
}
M.type = "dark"

M.polish_hl = {
  ["@function.builtin"] = { fg = M.base_30.cyan },
  ["@number"] = { fg = M.base_30.purple },
}
return M
