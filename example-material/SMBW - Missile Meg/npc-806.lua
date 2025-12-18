--NPCManager is required for setting basic NPC properties
local npcManager = require("npcManager")
local npcutils = require("npcs/npcutils")
--Create the library table
local sampleNPC = {}
--NPC_ID is dynamic based on the name of the library file
local npcID = NPC_ID

--Defines NPC config for our NPC. You can remove superfluous definitions.
local sampleNPCSettings = {
	id = npcID,
	--Sprite size
	gfxheight = 40,
	gfxwidth = 160,
	--Hitbox size. Bottom-center-bound to sprite size.
	width = 160,
	height = 32,
	--Sprite offset from hitbox for adjusting hitbox anchor on sprite.
	gfxoffsetx = 0,
	gfxoffsety = 8,
	--Frameloop-related
	frames = 2,
	framestyle = 1,
	framespeed = 8, --# frames between frame change
	--Movement speed. Only affects speedX by default.
	speed = 3,
	--Collision-related
	npcblock = false,
	npcblocktop = false, --Misnomer, affects whether thrown NPCs bounce off the NPC.
	playerblock = false,
	playerblocktop = true, --Also handles other NPCs walking atop this NPC.

	nohurt=false,
	nogravity = true,
	noblockcollision = true,
	nofireball = true,
	noiceball = false,
	noyoshi= false,
	nowaterphysics = false,
	--Various interactions
	jumphurt = true, --If true, spiny-like
	spinjumpsafe = false, --If true, prevents player hurt when spinjumping
	harmlessgrab = false, --Held NPC hurts other NPCs if false
	harmlessthrown = false, --Thrown NPC hurts other NPCs if false

	grabside=false,
	grabtop=false,

	--Identity-related flags. Apply various vanilla AI based on the flag:
	--iswalker = false,
	--isbot = false,
	--isvegetable = false,
	--isshoe = false,
	--isyoshi = false,
	--isinteractable = false,
	--iscoin = false,
	--isvine = false,
	--iscollectablegoal = false,
	--isflying = false,
	--iswaternpc = false,
	--isshell = false,

	--Emits light if the Darkness feature is active:
	--lightradius = 100,
	--lightbrightness = 1,
	--lightoffsetx = 0,
	--lightoffsety = 0,
	--lightcolor = Color.white,

	--Define custom properties below
	luahandlesspeed = true,
	fireeffect = npcID,
}

--Applies NPC settings
npcManager.setNpcSettings(sampleNPCSettings)

--Register the vulnerable harm types for this NPC. The first table defines the harm types the NPC should be affected by, while the second maps an effect to each, if desired.
npcManager.registerHarmTypes(npcID,
	{
		--HARM_TYPE_JUMP,
		--HARM_TYPE_FROMBELOW,
		--HARM_TYPE_NPC,
		--HARM_TYPE_PROJECTILE_USED,
		HARM_TYPE_LAVA,
		--HARM_TYPE_HELD,
		--HARM_TYPE_TAIL,
		--HARM_TYPE_SPINJUMP,
		HARM_TYPE_OFFSCREEN,
		--HARM_TYPE_SWORD
	}, 
	{
		--[HARM_TYPE_JUMP]=npcID,
		--[HARM_TYPE_FROMBELOW]=10,
		--[HARM_TYPE_NPC]=10,
		--[HARM_TYPE_PROJECTILE_USED]=10,
		[HARM_TYPE_LAVA]={id=13, xoffset=0.5, xoffsetBack = 0, yoffset=1, yoffsetBack = 1.5},
		--[HARM_TYPE_HELD]=10,
		--[HARM_TYPE_TAIL]=10,
		--[HARM_TYPE_SPINJUMP]=10,
		--[HARM_TYPE_OFFSCREEN]=10,
		--[HARM_TYPE_SWORD]=10,
	}
);

--Custom local definitions below
local STATE_NORMAL = 0
local STATE_STOODON = 1
local STATE_STOODON_DONTMOVE = 2
local frame = 0

--Register events
function sampleNPC.onInitAPI()
	npcManager.registerEvent(npcID, sampleNPC, "onTickEndNPC")
	--npcManager.registerEvent(npcID, sampleNPC, "onDrawNPC")
	--registerEvent(sampleNPC, "onNPCKill")
end

function sampleNPC.onTickEndNPC(v)
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
		data.state = STATE_NORMAL
		data.timer = 0
		data.stoodOn = false
	end

	--Depending on the NPC, these checks must be handled differently
	if v:mem(0x12C, FIELD_WORD) > 0    --Grabbed
	or v:mem(0x136, FIELD_BOOL)        --Thrown
	or v:mem(0x138, FIELD_WORD) > 0    --Contained within
	then
		--Handling
	end
	
	--Execute main AI. This template just jumps when it touches the ground.
	if data.state == STATE_NORMAL then
		if v.dontMove then
			v.direction = v.spawnDirection
		end
		
		frame = 0
		v.speedX = cfg.speed * v.direction
		v.animationFrame = npcutils.getFrameByFramestyle(v,{frame = frame})
		
		if not v.dontMove then
			data.timer = data.timer + 1
			if data.timer >= 4 then
				if v.direction == -1 then
					local poof = Effect.spawn(cfg.fireeffect, v.x + v.width - 24, v.y)
					poof.speedX = -0.75 * v.direction
				elseif v.direction == 1 then
					local poof = Effect.spawn(cfg.fireeffect, v.x - 16, v.y)
					poof.speedX = -0.75 * v.direction
				end
				data.timer = 0
			end
		end
		
		if player.standingNPC == v then
			data.timer = 0
			if not v.dontMove then
				data.state = STATE_STOODON
			else
				data.state = STATE_STOODON_DONTMOVE
				data.stoodOn = true
			end
			SFX.play(64)
			v.dontMove = false
			if v.direction == -1 then
				Effect.spawn(131, v.x + v.width - 24, v.y)
				Effect.spawn(73, v.x + v.width - 24, v.y)
			elseif v.direction == 1 then
				Effect.spawn(131, v.x - 16, v.y)
				Effect.spawn(73, v.x - 16, v.y)
			end
		end
	end
	
	if data.state == STATE_STOODON then
		frame = 1
		v.speedX = cfg.speed * v.direction
		v.speedY = 1
		v.animationFrame = npcutils.getFrameByFramestyle(v,{frame = frame})

		data.timer = data.timer + 1
		if data.timer >= 20 then
			if v.direction == -1 then
				Effect.spawn(10, v.x + v.width - 24, v.y)
			elseif v.direction == 1 then
				Effect.spawn(10, v.x - 16, v.y)
			end
			data.timer = 0
		end
	end
	
	if data.state == STATE_STOODON_DONTMOVE then
		frame = 0
		v.speedX = cfg.speed * v.direction
		v.animationFrame = npcutils.getFrameByFramestyle(v,{frame = frame})
		
		data.timer = data.timer + 1
		if data.timer >= 4 then
			if v.direction == -1 then
				local poof = Effect.spawn(806, v.x + v.width - 24, v.y)
				poof.speedX = -0.75 * v.direction
			elseif v.direction == 1 then
				local poof = Effect.spawn(806, v.x - 16, v.y)
				poof.speedX = -0.75 * v.direction
			end
			data.timer = 0
		end
		
		if player.standingNPC == nil then
			data.stoodOn = false
		end
		
		if data.stoodOn == false then
			if player.standingNPC == v then
				data.timer = 0
				data.state = STATE_STOODON
				SFX.play(64)
				if v.direction == -1 then
					Effect.spawn(131, v.x + v.width - 24, v.y)
					Effect.spawn(73, v.x + v.width - 24, v.y)
				elseif v.direction == 1 then
					Effect.spawn(131, v.x - 16, v.y)
					Effect.spawn(73, v.x - 16, v.y)
				end
			end
		end
	end
end

--Gotta return the library table!
return sampleNPC