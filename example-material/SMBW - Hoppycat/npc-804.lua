--NPCManager is required for setting basic NPC properties
local npcManager = require("npcManager")
local npcutils = require("npcs/npcutils")
local expandedDefines = require("expandedDefines")
--Create the library table
local hoppycat = {}
--NPC_ID is dynamic based on the name of the library file
local npcID = NPC_ID

--Defines NPC config for our NPC. You can remove superfluous definitions.
local hoppycatSettings = {
	id = npcID,
	--Sprite size
	gfxwidth = 48,
	gfxheight = 32,
	--Hitbox size. Bottom-center-bound to sprite size.
	width = 32,
	height = 32,
	--Sprite offset from hitbox for adjusting hitbox anchor on sprite.
	gfxoffsetx = 0,
	gfxoffsety = 2,
	--Frameloop-related
	frames = 4,
	framestyle = 1,
	framespeed = 12, --# frames between frame change
	--Movement speed. Only affects speedX by default.
	speed = 1,
	--Collision-related
	npcblock = false,
	npcblocktop = false, --Misnomer, affects whether thrown NPCs bounce off the NPC.
	playerblock = false,
	playerblocktop = false, --Also handles other NPCs walking atop this NPC.

	nohurt=false,
	nogravity = false,
	noblockcollision = false,
	nofireball = false,
	noiceball = false,
	noyoshi= false,
	nowaterphysics = false,
	--Various interactions
	jumphurt = true, --If true, spiny-like
	spinjumpsafe = true, --If true, prevents player hurt when spinjumping
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
	--isinteractable = true,
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
	jumpsound = "hoppycat-jump.ogg", --What do you think it's for?
	landsound = "hoppycat-land.ogg", --What do you think it's for?
	spotsound = "hoppycat-spot.ogg", --The sound for when the player is in sight
	losesound = "hoppycat-lose.ogg", --The sound for when the NPC loses sight of the player
}

--Applies NPC settings
npcManager.setNpcSettings(hoppycatSettings)

--Register the vulnerable harm types for this NPC. The first table defines the harm types the NPC should be affected by, while the second maps an effect to each, if desired.
npcManager.registerHarmTypes(npcID,
	{
		--HARM_TYPE_JUMP,
		HARM_TYPE_FROMBELOW,
		HARM_TYPE_NPC,
		HARM_TYPE_PROJECTILE_USED,
		HARM_TYPE_LAVA,
		HARM_TYPE_HELD,
		HARM_TYPE_TAIL,
		--HARM_TYPE_SPINJUMP,
		--HARM_TYPE_OFFSCREEN,
		HARM_TYPE_SWORD
	}, 
	{
		--[HARM_TYPE_JUMP]=900,
		[HARM_TYPE_FROMBELOW]=npcID,
		[HARM_TYPE_NPC]=npcID,
		[HARM_TYPE_PROJECTILE_USED]=npcID,
		[HARM_TYPE_LAVA]={id=13, xoffset=0.5, xoffsetBack = 0, yoffset=1, yoffsetBack = 1.5},
		[HARM_TYPE_HELD]=npcID,
		[HARM_TYPE_TAIL]=npcID,
		--[HARM_TYPE_SPINJUMP]=10,
		--[HARM_TYPE_OFFSCREEN]=10,
		[HARM_TYPE_SWORD]=npcID,
	}
);

--Custom local definitions below
local STATE_IDLE = 0
local STATE_SPOT = 1

--Register events
function hoppycat.onInitAPI()
	npcManager.registerEvent(npcID, hoppycat, "onTickEndNPC")
end

function hoppycat.onTickEndNPC(v)
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
		data.colX = v.x
		data.colY = v.y
		data.collider = Colliders.Circle(data.colX, data.colY, 304)
		data.playerJustIn = false
		--data.collider:Debug(true)
		data.state = STATE_IDLE
		data.jumpTimer = 60
		data.initialized = true
		data.frame = 0
		data.landSFX = true
		data.spotSFX = false
		data.loseSFX = true
	end
	
	--Always positions the collider to the NPC
	data.collider.x = data.colX
	data.collider.y = data.colY
	data.colX = v.x + (v.width / 2)
	data.colY = v.y + (v.height / 2)

	--Depending on the NPC, these checks must be handled differently
	if v:mem(0x12C, FIELD_WORD) > 0    --Grabbed
	or v:mem(0x136, FIELD_BOOL)        --Thrown
	or v:mem(0x138, FIELD_WORD) > 0    --Contained within
	then
		--Handling
	end
	
	npcutils.faceNearestPlayer(v)
	
	v.animationFrame = npcutils.getFrameByFramestyle(v, {frame = data.frame})
	
	--Jumping/Falling Animation
	if v.speedY < 0 then
		data.frame = 2
	elseif v.speedY > 0 then
		data.frame = 3
	end
	
	--Reduces the NPC's Gravity
	if v.speedY ~= 0 then
		v.speedY = v.speedY - 0.05
		data.spotSFX = true
	end

	if data.state == STATE_IDLE then
		if v.speedY == 0 then
			data.frame = 0
		end
	end

	--Jumps when the player jumps
	if data.state == STATE_SPOT then
		data.loseSFX = false
		
		data.jumpTimer = data.jumpTimer + 1
		
		--Animation stuff
		if v.speedY == 0 then
			data.frame = 1
		end
		
		--Checks if the player is jumping
		if v.collidesBlockBottom and (player.keys.jump == KEYS_PRESSED or player.keys.altJump == KEYS_PRESSED) and not player:mem(0x36, FIELD_BOOL) and player.speedY < 0 then
			data.jumpTimer = 0
		end
		
		if v.collidesBlockBottom then
			if not data.landSFX then
				SFX.play(cfg.landsound)
				data.landSFX = true
			end
		end
		
		--Delays the jump by a bit
		if data.jumpTimer == 3 then
			v.speedX = 0
			v.speedY = -10
			SFX.play(cfg.jumpsound)
			data.landSFX = false
		end
		
		for _,block in ipairs(Block.getIntersecting(v.x + 6, v.y - 4, v.x + v.width - 6, v.y)) do
			if block.MEGA_HIT_MAP then
				block:hit()
			end
		end
		
		if v.collidesBlockUp then
			SFX.play(3)
			v.speedY = 0
		end
	end
	
	--Changes the state when the player is in the NPC's range
	if Colliders.collide(data.collider, player) then
		data.state = STATE_SPOT
		if not data.spotSFX and v.speedY == 0 then
			SFX.play(cfg.spotsound)
			data.spotSFX = true
		end
	else
		data.state = STATE_IDLE
		data.spotSFX = false
		if not data.loseSFX and v.speedY == 0 then
			SFX.play(cfg.losesound)
			data.loseSFX = true	
		end
	end
end

--Gotta return the library table!
return hoppycat