#include <memory>
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include "lifecycle_msgs/msg/transition_event.hpp"

class Listener : public rclcpp::Node{
    public:
        explicit Listener(const std::string & nodeName) : Node(node_name)
        {
            messageSubscription = this->create_subscription<std_msgs::msg::String>(
                "messages",
                10,
                std::bind(&Listener::messageCallback, this, std::placeholders::_1) //takes a function with some arguments and returns a new callable object, later calls the function when that object is invoked
            )
            notificationSubscription = this->create_subscription<std_msgs::msg::String>(
                "lc_talker/transition_event",
                10,
                std::bind(&Listener::notificationCallback, this, std::placeholders::_1) //takes a function with some arguments and returns a new callable object, later calls the function when that object is invoked
            )
        }
        void messageCallback(const std_msgs::msg::String::SharedPtr msg){
            RCLCPP_INFO(get_logger(), "messageCallback: %s", msg->data.c_str());
        }
        void notificationCallback(const lifecycle_msgs::msg::TransitionEvent::SharePtr msg){
            RCLCPP_INFO(get_logger(), "notificationCallback: transition from state %s to %s",
            msg->start_state.c_str(),
            msg->goal_state.label.c_str());
        }
    private:
        std::shared_ptr<rclcpp::Subscription<std_msgs::msg::String>> messageSubscription; //This line declares a shared pointer(a smart pointer that keeps track of how many shared pointer instances currently point to the same object. With this we don't have to manually track when to delete the object) that holds subscription to the topic of template std_msgs:msg:String 
        std::shared_ptr<rclcpp::Subscription<lifecycle_msgs::msg::TransitionEvent>> notificationSubscription;

};
int main(int argc, char ** argv){
    rclcpp::init(argc, argv);
    auto listenerNode = std::make_shared<Listener>("listener_node");
    rclcpp::spin(listenerNode);

    rclcpp::shutdown();
    return 0;
}