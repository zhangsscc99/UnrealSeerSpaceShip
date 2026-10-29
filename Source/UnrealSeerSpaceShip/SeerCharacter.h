#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SeerCharacter.generated.h"

class UCameraComponent;
class UInputAction;
class UInputMappingContext;
class USpringArmComponent;
struct FInputActionValue;

/**
 * Player character for the lab, with a third-person chase camera.
 *
 * Desktop: WASD walks (camera-relative), mouse orbits, Space jumps (twice for a
 * double jump), C toggles the near/far camera preset.
 * Mobile: the default touch interface's left virtual joystick moves; a drag that
 * starts on the right half of the screen orbits the camera.
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

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<UCameraComponent> FollowCamera;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> MoveAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TArray<TObjectPtr<UInputMappingContext>> MappingContexts;

private:
	void Move(const FInputActionValue& Value);
	void MoveForward(float Value);
	void MoveRight(float Value);

	void Turn(float Value);
	void LookUp(float Value);
	void TurnRate(float Value);
	void LookUpRate(float Value);
	void CycleCamera();

	void TouchStarted(ETouchIndex::Type FingerIndex, FVector Location);
	void TouchMoved(ETouchIndex::Type FingerIndex, FVector Location);
	void TouchEnded(ETouchIndex::Type FingerIndex, FVector Location);

	void ApplyLookDelta(float DeltaYaw, float DeltaPitch);
	void ApplyCameraPreset(int32 Index);

	int32 CameraPreset = 0;
	ETouchIndex::Type LookFinger = ETouchIndex::MAX_TOUCHES;
	ETouchIndex::Type JumpFinger = ETouchIndex::MAX_TOUCHES;
	FVector2D LastTouchLocation = FVector2D::ZeroVector;
};
