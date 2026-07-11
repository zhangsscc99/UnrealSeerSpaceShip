#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "KlosePlayerController.generated.h"

UCLASS()
class UNREALSEERSPACESHIP_API AKlosePlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	AKlosePlayerController();

protected:
	virtual void BeginPlay() override;
	virtual void OnPossess(APawn* InPawn) override;

	void ApplyGameInputMode();
};
