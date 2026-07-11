#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "KloseThirdPersonCharacter.generated.h"

class USpringArmComponent;
class UCameraComponent;
class UStaticMeshComponent;

UCLASS()
class UNREALSEERSPACESHIP_API AKloseThirdPersonCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AKloseThirdPersonCharacter();

protected:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<UCameraComponent> FollowCamera;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Visual")
	TObjectPtr<UStaticMeshComponent> BodyMesh;
};
