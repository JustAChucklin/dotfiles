-- ~/.config/yazi/plugins/full-details.yazi/init.lua
function setup()
	local style = ui.Style():fg("blue")

	Linemode:children_add(function(self)
		local h = self._file:cha().host
		local permissions = self._file:cha():perm() or ""
		local size = self._file:size() and ui.Span(ya.readable_size(self._file:size())):style(style) or ""
		local mtime = os.date("%Y-%m-%d %H:%M", math.floor(self._file:cha().mtime or 0))

		return {
			ui.Span(permissions .. " "),
			size,
			ui.Span(" " .. mtime),
		}
	end, 500)
end
