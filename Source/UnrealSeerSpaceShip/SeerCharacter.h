#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SeerCharacter.generated.h"

class UCameraComponent;
class UInputAction;
class UInputMappingContext;
struct FInputActionValue;

/**
 * Player character for the 2.5D lab.
 *
 * Differences from the flying SpectatorPawn it replaces: CharacterMovement gives it
 * gravity and floor collision (no vertical drift), and bOrientRotationToMovement turns
 * the body towards the direction it walks. The camera is absolute, so the view never
 * moves even though the character rotates and walks around underneath it.
 */
UCLASS()
class UNREALSEERSPACESHIP_API ASeerCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	ASeerCharacter();

protected:
	virtual void BeginPlay() override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

	/** Absolute world transform: the view stays put while the character moves. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<UCameraComponent> FixedCamera;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> MoveAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TArray<TObjectPtr<UInputMappingContext>> MappingContexts;

private:
	void Move(const FInputActionValue& Value);
	void MoveForward(float Value);
	void MoveRight(float Value);
};
