#include "KlosePlayerController.h"

AKlosePlayerController::AKlosePlayerController()
{
	bShowMouseCursor = false;
	bEnableClickEvents = false;
	bEnableMouseOverEvents = false;
}

void AKlosePlayerController::BeginPlay()
{
	Super::BeginPlay();
	ApplyGameInputMode();
}

void AKlosePlayerController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);
	ApplyGameInputMode();
}

void AKlosePlayerController::ApplyGameInputMode()
{
	FInputModeGameOnly InputMode;
	SetInputMode(InputMode);
	SetIgnoreLookInput(false);
	SetIgnoreMoveInput(false);
}
