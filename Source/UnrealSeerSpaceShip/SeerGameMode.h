#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "SeerGameMode.generated.h"

/**
 * GameMode for the lab: wires the Seer pawn and the touch HUD together in C++
 * so nothing depends on editing Blueprint class defaults.
 */
UCLASS()
class UNREALSEERSPACESHIP_API ASeerGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ASeerGameMode();
};
