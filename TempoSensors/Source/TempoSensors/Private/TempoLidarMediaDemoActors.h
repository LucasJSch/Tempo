// Copyright Tempo Simulation, LLC. All Rights Reserved

#pragma once

#include "TempoCamera.h"
#include "TempoLidar.h"

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "TempoLidarMediaDemoActors.generated.h"

class UExponentialHeightFogComponent;
class ULocalFogVolumeComponent;

// Demo-only specialization so the level's authored defaults do not become the production lidar's
// defaults. It remains a UTempoLidar for discovery and RPC property editing.
UCLASS(NotBlueprintable)
class UTempoLidarMediaDemoLidar : public UTempoLidar
{
	GENERATED_BODY()

public:
	UTempoLidarMediaDemoLidar();
};

// A camera and lidar with identical poses. Kept as native components so the plugin-owned demo map
// has no dependency on a host project's Blueprint classes.
UCLASS(NotBlueprintable)
class ATempoLidarMediaDemoRig : public AActor
{
	GENERATED_BODY()

public:
	ATempoLidarMediaDemoRig();

private:
	UPROPERTY(VisibleAnywhere)
	TObjectPtr<USceneComponent> SceneRoot;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UTempoCamera> TempoCamera;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UTempoLidarMediaDemoLidar> TempoLidar;
};

// Groups the ambient height fog and localized fog sphere under one actor, allowing the demo client
// to hide/show the entire fog path with one SetActorHiddenInGame call.
UCLASS(NotBlueprintable)
class ATempoLidarMediaDemoFog : public AActor
{
	GENERATED_BODY()

public:
	ATempoLidarMediaDemoFog();

private:
	UPROPERTY(VisibleAnywhere)
	TObjectPtr<USceneComponent> SceneRoot;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UExponentialHeightFogComponent> HeightFog;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<ULocalFogVolumeComponent> LocalFog;
};
