function Linemode:custom()
	local year = os.date("%Y")
	local mtime = os.date("%b %d %H:%M", math.floor(self._file.cha.mtime or 0))
	local size = self._file:size()
	local res = ""

	-- 1. Permissions
	res = res .. tostring(self._file.cha:perm() or "") .. " "

	-- 2. Size (Human readable)
	if size then
		res = res .. ya.readable_size(size) .. " "
	end

	-- 3. Date
	res = res .. mtime

	return ui.Line(res)
end
