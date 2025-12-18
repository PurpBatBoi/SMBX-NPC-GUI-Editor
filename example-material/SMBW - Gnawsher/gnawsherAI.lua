--NPCManager is required for setting basic NPC properties
local npcManager = require("npcManager")
local npcutils = require("npcs/npcutils")

--Create the library table
local gnawsher = {}

--NPC_ID is dynamic based on the name of the library file
local npcID = NPC_ID
local npcIDs = {}

--Custom local definitions below
local STATE_FLY = 0
local STATE_CHOMP = 1
local STATE_CHOMPED = 2

--Register events
function gnawsher.register(id)
	npcManager.registerEvent(id, gnawsher, "onTickEndNPC")
	
	--npcIDs[id] = true
end

--Register events
function gnawsher.onInitAPI()
	registerEvent(gnawsher, "onNPCKill")
end

function gnawsher.onTickEndNPC(v)
	--Don't act during time freeze
	if Defines.levelFreeze then return end
	
	local data = v.data
	local cfg = NPC.config[v.id]
	
	--If despawned
	if v.despawnTimer <= 0 then
		--Reset our properties, if necessary
		data.initialized = false
		return
	end

	--Initialize
	if not data.initialized then
		--Initialize necessary data.
		data.initialized = true
		
		data.frame = 0
		
		data.timer = 0
		data.animTimer = 0
		data.chompTimer = 0
		data.lerpTimer = 0
		
		data.left = data.left or 0
		data.right = data.right or 0
		data.up = data.up or 0
		data.down = data.down or 0
		
		data.state = STATE_FLY
	end

	--Depending on the NPC, these checks must be handled differently
	if v:mem(0x12C, FIELD_WORD) > 0    --Grabbed
	or v:mem(0x136, FIELD_BOOL)        --Thrown
	or v:mem(0x138, FIELD_WORD) > 0    --Contained within
	then
		--Handling
	end
	
	if cfg.horizontal then
		if v.direction == -1 then
			data.left = v.x - 4
			data.right = v.x + v.width - 4
			data.up = v.y + 8
			data.down = v.y + v.height - 8
		elseif v.direction == 1 then
			data.left = v.x + 4
			data.right = v.x + v.width + 4
			data.up = v.y + 8
			data.down = v.y + v.height - 8
		end
	elseif cfg.vertical then
		if v.direction == -1 then
			data.left = v.x + 8
			data.right = v.x + v.width - 8
			data.up = v.y - 4
			data.down = v.y + v.height - 4
		elseif v.direction == 1 then
			data.left = v.x + 8
			data.right = v.x + v.width - 8
			data.up = v.y + 4
			data.down = v.y + v.height + 4
		end
	end

	if data.state == STATE_FLY then
		data.animTimer = data.animTimer + 1
		
		--Biting Animation
		if data.animTimer < 8 then
			data.frame = 0
		elseif data.animTimer >= 8 and data.animTimer < 16 then
			data.frame = 1
		elseif data.animTimer >= 16 then
			data.animTimer = 0
		end
		
		if data.animTimer == 15 then
			SFX.play("gnawsher-chase"..RNG.randomInt(1,4)..".ogg")
		end
		
		if cfg.horizontal then
			v.speedX = cfg.speed * v.direction
		elseif cfg.vertical then
			v.speedY = cfg.speed * v.direction
		end
		
		--Checks for blocks in-front of the NPC
		for _,block in ipairs(Block.getIntersecting(data.left, data.up, data.right, data.down)) do
			if block.isHidden == false and block:mem(0x5a, FIELD_WORD) == 0 and (Block.config[block.id].bumpable or Block.config[block.id].smashable) then
				v.speedX = 0
				v.speedY = 0
				data.state = STATE_CHOMP
				data.animTimer = 0
			end
		end
		
		--Checks for other NPCs in-front of the NPC
		for _,npc in ipairs(NPC.getIntersecting(data.left, data.up, data.right, data.down)) do
			if npc.id ~= 808 and npc.id ~= 809 and not npc.friendly and not npc.isGenerator and not NPC.config[npc.id].isvine and (not NPC.config[npc.id].npcblock or not NPC.config[npc.id].playerblock) then
				v.speedX = 0
				v.speedY = 0
				data.state = STATE_CHOMP
				data.animTimer = 0
				npc.dontMove = true
			end
		end
	end
	
	if data.state == STATE_CHOMP then
		data.timer = data.timer + 1
		
		if data.timer < 18 then
			data.frame = 1
		elseif data.timer >= 18 then
			--Remove any blocks in-front of the NPC
			for _,block in ipairs(Block.getIntersecting(data.left, data.up, data.right, data.down)) do
				if block.isHidden == false and block:mem(0x5a, FIELD_WORD) == 0 and (Block.config[block.id].bumpable or Block.config[block.id].smashable) then
					block:remove(true)
				end
			end
			
			--Remove any other NPCs in-front of the NPC
			for _,npc in ipairs(NPC.getIntersecting(data.left, data.up, data.right, data.down)) do
				if npc.id ~= 808 and npc.id ~= 809 and not npc.friendly and not npc.isGenerator and not NPC.config[npc.id].isvine then
					npc:kill(9)
					--Effect.spawn(1, v.x, v.y)
				end
			end
			
			data.frame = 0
			SFX.play("gnawsher-bite.ogg")
			data.state = STATE_CHOMPED
			data.timer = 0
		end
		
		if data.timer >= 9 then
			--Makes the block/NPC removal look less weird :)
			data.lerpTimer = data.lerpTimer + 0.017
			if cfg.horizontal then
				v.x = math.lerp(v.x, v.x + (32 * v.direction), data.lerpTimer)
			elseif cfg.vertical then
				v.y = math.lerp(v.y, v.y + (32 * v.direction), data.lerpTimer)
			end
		end
	end
	
	if data.state == STATE_CHOMPED then
		data.timer = data.timer + 1
		data.frame = 0
		if data.timer >= 20 then
			data.frame = 0
			data.state = STATE_FLY
			data.timer = 0
			data.lerpTimer = 0
		end
	end

	--Text.print(data.timer, 10, 10)
	
	v.animationFrame = npcutils.getFrameByFramestyle(v, {frame = data.frame})
end

function gnawsher.onNPCKill(event, v, reason)
	if v.id ~= 808 and v.id ~= 809 then return end
	
	if reason ~= 8 and reason ~= 9 and reason ~= 10 then
		SFX.play("gnawsher-find.ogg")
	end
end

--Gotta return the library table!
return gnawsher