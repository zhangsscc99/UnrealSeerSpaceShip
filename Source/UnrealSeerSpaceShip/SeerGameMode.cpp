#include "SeerGameMode.h"

#include "SeerCharacter.h"
#include "SeerHUD.h"

ASeerGameMode::ASeerGameMode()
{
	DefaultPawnClass = ASeerCharacter::StaticClass();
	HUDClass = ASeerHUD::StaticClass();
}
