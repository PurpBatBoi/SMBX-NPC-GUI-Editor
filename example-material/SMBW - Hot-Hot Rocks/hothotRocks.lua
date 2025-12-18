local npcManager = require("npcManager")

local hothotRocks = {}

local npcIDs = {}

local timer = 49

local STATE_NORMAL = 0
local STATE_EXTINGUISHED = 1

--Register events
function hothotRocks.register(id)
	npcManager.registerEvent(id, hothotRocks, "onTickEndNPC")
	registerEvent(hothotRocks, "onTickEnd")
	
	npcIDs[id] = true
end

function hothotRocks.onTickEnd(v)
	timer = timer + 0.5
end

function hothotRocks.onTickEndNPC(v)
	--Don't act during time freeze
	if Defines.levelFreeze then return end
	
	local data = v.data
	local cfg = NPC.config[v.id]
	
	--If despawned
	if v.despawnTimer <= 0 then
		return
	end
	
	--Initialize
	if not data.initialized then
		--Initialize necessary data.
		data.initialized = true
		data.hitterbox = Colliders.Rect(v.x + cfg.width / 2, v.y + cfg.width / 2, cfg.colliderSize, cfg.colliderSize, 0)
		--data.hitterbox:Debug(true)
		data.canHurt = false
		data.state = 0
		cfg.ishot = false
	end

	--Depending on the NPC, these checks must be handled differently
	if v:mem(0x12C, FIELD_WORD) > 0    --Grabbed
	or v:mem(0x136, FIELD_BOOL)        --Thrown
	or v:mem(0x138, FIELD_WORD) > 0    --Contained within
	then
		--Handling
	end
	
	if data.state == STATE_NORMAL then
		--timer checking for being able to hurt the player and stuff
		if timer < 195 then
			data.canHurt = false
		elseif timer >= 195 then
			data.canHurt = true
		end
		if timer >= 390 then
			SFX.play(88)
			timer = -65
			data.canHurt = false
		end
		if timer == 195 then
			SFX.play(42)
		end
		
		--animation stuff
		if timer < 49 then
			v.animationFrame = 0
		elseif timer >= 49 and timer < 98 then
			v.animationFrame = 1
		elseif timer >= 98 and timer < 147 then
			v.animationFrame = 2
		elseif timer >= 147 and timer < 195 then
			v.animationFrame = 3
		elseif timer >= 195 and timer < 203 then
			v.animationFrame = 4
		elseif timer >= 203 and timer < 385 then
			v.animationFrame = 5
		elseif timer >= 385 then
			v.animationFrame = 2
		end
		
		--if it's hot then it can damage you but if its not then its not hot and its so dull with no light :(
		if data.canHurt == true then
			cfg.ishot = true
			cfg.lightbrightness = 1
			if Colliders.collide(data.hitterbox, player) then
				player:harm()
			end
		else
			cfg.ishot = false
			cfg.lightbrightness = 0
		end
		
		--if something cold touches it EXTINGUOOOOIIIUUUUSSHHHHHHGYYEEAAAAAAAHHHHHHHHHHHHHHHHHH!!!!!!!!!!!!!!!!!!
		for _,npc in ipairs (NPC.getIntersecting(v.x - 2, v.y - 2, v.x + cfg.colliderSize + 2, v.y + cfg.colliderSize + 2)) do
			if NPC.config[npc.id].isCold then
				npc:kill()
				data.state = 1
				SFX.play(88)
			end
		end
	end
	
	if data.state == STATE_EXTINGUISHED then
		data.canHurt = false
		v.animationFrame = 6
	end
end

return hothotRocks