---@type ChadrcConfig 

local M = {}

M.ui = {
  theme = 'dracula-pro',
  hl_override = {
    NvDashAscii = {
      bg = 'none',
      fg = '#bd93f9',
    },
    NvDashButtons = {
      bg = 'none',
      fg = '#bd93f9',
    },
  },
  transparency = true,
  nvdash = {
    load_on_startup = true,
    header = require "custom.functions".randomsplash()
  },
  statusline = {
    theme = "minimal",
    separator_style = "default",
    override_module = nil,
  }
}

M.mappings = require "custom.mappings"
M.plugins = "custom.plugins"

return M
