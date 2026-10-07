// Copyright Tempo Simulation, LLC. All Rights Reserved

#include "TempoLidarMediaDemoActors.h"

#include "Components/ExponentialHeightFogComponent.h"
#include "Components/LocalFogVolumeComponent.h"

UTempoLidarMediaDemoLidar::UTempoLidarMediaDemoLidar()
{
	MinDistance = 50.0;
	MaxDistance = 3000.0;
	IntensitySaturationDistance = 800.0;
	VerticalFOV = 24.0;
	HorizontalFOV = 100.0;
	VerticalBeams = 48;
	HorizontalBeams = 320;
	BeamDivergence = 0.3;
	bSimulateParticipatingMedia = true;
	bMediaIncludesTranslucency = true;
	MediaExtinctionScale = 1.0f;
	MediaBackscatter = 0.18f;
	MinDetectableIntensity = 0.005f;
	bStochasticMediaReturns = true;
	MediaRangeBins = 64;
	ReturnMode = ETempoLidarReturnMode::Dual;
}

ATempoLidarMediaDemoRig::ATempoLidarMediaDemoRig()
{
	SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
	SetRootComponent(SceneRoot);

	TempoCamera = CreateDefaultSubobject<UTempoCamera>(TEXT("TempoCamera"));
	TempoCamera->SetupAttachment(SceneRoot);
	TempoCamera->FOVAngle = 100.0f;

	TempoLidar = CreateDefaultSubobject<UTempoLidarMediaDemoLidar>(TEXT("TempoLidar"));
	TempoLidar->SetupAttachment(SceneRoot);
}

ATempoLidarMediaDemoFog::ATempoLidarMediaDemoFog()
{
	SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
	SetRootComponent(SceneRoot);

	HeightFog = CreateDefaultSubobject<UExponentialHeightFogComponent>(TEXT("HeightFog"));
	HeightFog->SetupAttachment(SceneRoot);
	HeightFog->SetFogDensity(0.002f);
	HeightFog->SetFogHeightFalloff(0.05f);
	HeightFog->SetVolumetricFog(true);
	HeightFog->SetVolumetricFogDistance(3000.0f);
	HeightFog->SetVolumetricFogExtinctionScale(0.7f);
	HeightFog->SetVolumetricFogAlbedo(FColor(220, 230, 235));

	LocalFog = CreateDefaultSubobject<ULocalFogVolumeComponent>(TEXT("LocalFog"));
	LocalFog->SetupAttachment(SceneRoot);
	LocalFog->SetRelativeScale3D(FVector(0.65));
	LocalFog->SetRadialFogExtinction(2.2f);
	LocalFog->SetHeightFogExtinction(0.8f);
	LocalFog->SetFogAlbedo(FLinearColor(0.82f, 0.88f, 0.92f));
}
