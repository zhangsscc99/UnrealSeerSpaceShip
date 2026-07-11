#include "KloseGameMode.h"

#include "KlosePlayerController.h"
#include "KloseThirdPersonCharacter.h"

AKloseGameMode::AKloseGameMode()
{
	DefaultPawnClass = AKloseThirdPersonCharacter::StaticClass();
	PlayerControllerClass = AKlosePlayerController::StaticClass();
}
