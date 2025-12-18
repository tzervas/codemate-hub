package main

import (
	"context"
	"flag"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	// TODO: GPU-002 - Implement allocator package
	// "github.com/tzervas/codemate-hub/services/gpu-resource-manager/pkg/allocator"
	// TODO: GPU-002 - Implement monitor package
	// "github.com/tzervas/codemate-hub/services/gpu-resource-manager/pkg/monitor"
)

func main() {
	configPath := flag.String("config", "/config/strategy.yaml", "Path to strategy configuration")
	flag.Parse()

	log.Println("Starting GPU Resource Manager (v2.0)...")

	// TODO: GPU-002 - Initialize NVML Detector (Task GPU-001)
	// detector, err := allocator.NewDetector()
	// if err != nil {
	// 	log.Fatalf("Failed to initialize NVML detector: %v", err)
	// }
	// defer detector.Shutdown()

	// TODO: GPU-002 - Load Capabilities
	// caps, err := detector.DetectCapabilities()
	// if err != nil {
	// 	log.Fatalf("Failed to detect GPU capabilities: %v", err)
	// }
	// log.Printf("Detected GPU: %s (%d MB VRAM)", caps.Name, caps.TotalVRAM/1024/1024)

	// TODO: GPU-010 - Start Metrics Server
	// go monitor.StartMetricsServer(":9090")

	// 4. Main Loop
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	log.Printf("GPU Resource Manager started with config: %s", *configPath)
	log.Println("Waiting for shutdown signal...")

	<-ctx.Done()
	log.Println("Shutting down GPU Resource Manager...")

	// Graceful cleanup
	_, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	log.Println("GPU Resource Manager stopped")
}
